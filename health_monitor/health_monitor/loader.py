from click import get_network_bw
from mt_snmp import concurrent_snmp_query
from objects import Port
from database import get_mysql_db
from utils import locked_subnet

import tele
import json
import logging
import sys

# === CONSTANTS
logger = logging.getLogger("health-monitor")
logger.setLevel(logging.INFO)


def get_databases():
    try:
        conn1 = get_mysql_db(db="proveedores")
        cursor1 = conn1.cursor()
        conn2 = get_mysql_db(db="monitor")
        cursor2 = conn2.cursor()
        return conn1, conn2, cursor1, cursor2
    except Exception as e:
        logger.exception(e)
        send_error("No se pudo conectar a la base MySQL (monitor, proveedores)")


def get_excluded_subnets(cursor):
    logger.info("Obteniendo subredes excluidas manualmente del proceso.")
    prefixes = []
    sql = "SELECT prefix FROM exclusiones"
    cursor.execute(sql)
    for row in cursor.fetchall():
        prefixes.append(row[0])

    logger.info("Obteniendo subredes excluidas por haber sido movidas en los ultimos 30min.")
    sql = "SELECT timestamp,prefix FROM moved_prefixes WHERE status IN ('commit','rollback','finished')"
    cursor.execute(sql)
    for row in cursor.fetchall():
        ts = row[0]
        if locked_subnet(ts):
            logger.warning(f"Subred {row[1]} bloqueada debido a movimiento reciente (<30 min)")
            prefixes.append(row[1])

    logger.info(f"Se encontraron {len(prefixes)} prefijos excluidos.")
    return prefixes


def get_moved_networks(cursor, conn):
    # === Elimina registros pendientes, no fueron tomados en cuenta
    logger.info("Eliminando de la base los prefijos en estado pendiente de la anterior ejecución.")
    sql = "DELETE FROM moved_prefixes WHERE status='pending'"
    cursor.execute(sql)
    conn.commit()

    # === Hace downgrade de pending-rollback a rollback, no fueron tomados en cuenta.
    logger.info("Degradando status de prefijos que estaban listos para rollback, para que sean revisados nuevamente.")
    sql = "UPDATE moved_prefixes SET status='rollback' WHERE status='pending-rollback'"
    cursor.execute(sql)
    conn.commit()

    logger.info("Obteniendo prefijos con status commit y rollback.")
    moved = dict()
    sql = "SELECT prefix,from_router,from_port FROM moved_prefixes WHERE status IN ('commit','rollback','pending-rollback')"
    cursor.execute(sql)
    for row in cursor.fetchall():
        gate = f"{row[1]}:{row[2]}"
        if gate in moved:
            moved[gate].append(row[0])
        else:
            moved[gate] = []
            moved[gate].append(row[0])
    return moved


def find_unlocked_subnets(cursor):
    logger.info("=== Buscando subredes que deban volver a su salida original.")
    devolver = []
    # === Devuelve los prefijos listos para retornar
    sql = "SELECT to_router, to_port, prefix, from_router, from_port, token, subnet_bw_at FROM moved_prefixes WHERE status='rollback'"
    cursor.execute(sql)
    for row in cursor.fetchall():
        salida_actual = Port(router=row[0], name=row[1])
        prefix = {
            'gbps': get_network_bw(salida_actual.gate, row[2]),
            'net': row[2],
            'recorded_gbps': row[6]
        }
        salida_anterior = Port(router=row[3], name=row[4])
        devolver.append((salida_actual, prefix, salida_anterior, row[5]))
    return devolver


def update_db_subnet_counters(cursor, conn):
    logger.info("Incrementando el counter de los prefijos que han sido movidos. Cambiando status de prefijos con counter > 6 a rollback")
    # === Incrementa el counter de subredes movidas
    sql = "UPDATE moved_prefixes SET status_counter=status_counter + 1 WHERE status_counter < 6 AND status='commit'"
    cursor.execute(sql)
    conn.commit()

    sql = "UPDATE moved_prefixes SET status='rollback' WHERE status_counter>=6 AND status='commit'"
    cursor.execute(sql)
    conn.commit()


def update_db_monitor(gates, cursor, conn):
    logger.info("Actualizando status de salidas seleccionadas en base de datos")
    # === Elimina posibles salidas que ya no existan
    sql = "DELETE FROM current_state"
    cursor.execute(sql)
    conn.commit()

    # === Actualiza la informacion
    sql = f"INSERT INTO current_state(`router`,`port`,`current_bw`,`load`,`status`) VALUES"
    for gate, params in gates.items():
        sql += f" ('{params.router}','{params.name}',{params.current_gbps},{params.load},'ACTIVE'),"

    if sql.endswith(","):
        sql = sql[:-1]
    cursor.execute(sql)
    conn.commit()
    return gates


def update_db_monitor_movement(gates, cursor, conn):
    logger.info("Actualizando status de salidas en saturacion en base de datos")
    # === Actualiza la informacion
    sql = f"INSERT INTO monitor_logs(`router`,`port`,`current_bw`,`load`,`status`) VALUES"
    for gate, params in gates.items():
        sql += f" ('{params.router}','{params.name}',{params.current_gbps},{params.load},'ACTIVE'),"

    if sql.endswith(","):
        sql = sql[:-1]
    cursor.execute(sql)
    conn.commit()
    return


async def get_active_gates(cursor):
    logger.info("Obteniendo las salidas que participan en el proceso de movimiento automatico")
    gates = dict()
    gates_list = []
    sql = "SELECT router,puerto,nombre,capacidad,peer_v4,threshold,optimal_thold,optimal_priority,os_type FROM proveedor WHERE tipo='INTERNET' AND enabled=1 AND polling=1"
    cursor.execute(sql)
    rows = cursor.fetchall()
    for row in rows:
        gate = f"{row[0]}:{row[1]}"
        if gate not in gates_list:
            gates_list.append(gate)
    capacidad_snmp, snmp_ids, status = await concurrent_snmp_query(gates_list)

    for row in rows:
        gate = f"{row[0]}:{row[1]}"
        if status.get(gate, "down") == "up":
            capacidad_db = int(row[3].replace("GB", "").strip())
            capacidad_actual = int(capacidad_snmp.get(gate, 999999999999999999))  # === Si no lo encuentra en el dict que escoja el valor de la base
            logger.debug(f"Gate {gate} = {capacidad_actual}")

            optimal_thold = row[6] if row[6] != 100 else row[5]
            if capacidad_actual == 0 or capacidad_db == 0:
                logger.error(f"Salida {gate} esta caída, por favor verificar. Capacidad actual consultada por SNMP=0")
            elif capacidad_actual < capacidad_db and "rointndtl" not in gate: # Bypass por problema de maximo de capacidad
                tele.send(f"Se detecta una capacidad menor a la registrada en base de datos en la salida {gate} ({capacidad_actual}/{capacidad_db}).")
                logger.warning(
                    f"Se detecta una capacidad menor a la registrada en base de datos en la salida {gate}. Sobreescribiendo capacidad real a {capacidad_actual}")
                gates[gate] = Port(router=row[0], name=row[1], proveedor=row[2], capacidad=capacidad_actual, peer_v4=row[4], threshold=row[5],
                                   snmp_id=snmp_ids.get(gate, 0), optimal_thold=optimal_thold, optimal_priority=row[7], os_type=row[8])
            else:
                gates[gate] = Port(router=row[0], name=row[1], proveedor=row[2], capacidad=capacidad_db, peer_v4=row[4], threshold=row[5],
                                   snmp_id=snmp_ids.get(gate, 0), optimal_thold=optimal_thold, optimal_priority=row[7], os_type=row[8])
        else:
            logger.warning(f"Se detecta que la salida {gate} esta admin-down.")

    router_puertos = get_router_puertos(cursor)
    return gates, router_puertos


def get_router_puertos(cursor):
    d = {}
    sql = "SELECT router,puerto,os_type FROM proveedor WHERE tipo='INTERNET' AND enabled=1 AND polling=1"
    cursor.execute(sql)
    for row in cursor.fetchall():
        if row[0] in d:
            d[row[0]]['puertos'].append(row[1])
        else:
            d[row[0]] = {'os_type': row[2], 'puertos': []}
            d[row[0]]['puertos'].append(row[1])
    return d


# def match_l*ck_counters(gates, cursor):
#     sql = "SELECT router,port,status_counter FROM current_state WHERE status='L*CKED'"
#     cursor.execute(sql)
#     for row in cursor.fetchall():
#         gate = f"{row[0]}:{row[1]}"
#         if gate in gates:
#             gates[gate].l*cked = True
#             gates[gate].counter = int(row[2]) + 1  # === Incrementa el counter de l*cked
#             # === Si el counter llega a 4 se desbloquea (3 intentos = 15 minutos)
#             if gates[gate].counter >= 4:
#                 logger.info(f"Se ha desbloqueado la salida {gates[gate].gate} por haber pasado mas de 15 minutos desde ultimo movimiento.")
#                 gates[gate].l*cked = False
#                 gates[gate].counter = 0
#     return


def expand(port):
    if port.startswith("Po") and not port.startswith("Port-channel"):
        return port.replace("Po", "Port-channel")
    if port.startswith("Hu") and not port.startswith("HundredGigE"):
        return port.replace("Hu", "HundredGigE")
    if port.startswith("Te") and not port.startswith("TenGigabitEthernet") and not port.startswith("TenGigE"):
        return port.replace("Te", "TenGigabitEthernet")
    if port.startswith("Gi") and not port.startswith("GigabitEthernet"):
        return port.replace("Gi", "GigabitEthernet")
    if port.startswith("Fa") and not port.startswith("FastEthernet"):
        return port.replace("Fa", "FastEthernet")
    if port.startswith("BE"):
        return port.replace("BE", "Bundle-Ether")
    if port.startswith("Vl") and not port.startswith("Vlan"):
        return port.replace("Vl", "Vlan")
    return port


def send_error(msg):
    rs = {"status": "error", "error": msg}
    print(json.dumps(rs))
    sys.exit(0)
