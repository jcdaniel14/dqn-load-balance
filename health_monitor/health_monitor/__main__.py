from loader import get_active_gates, get_excluded_subnets, update_db_monitor, update_db_monitor_movement, update_db_subnet_counters, find_unlocked_subnets, get_moved_networks, \
    get_databases
from click import find_top_subnets, generate_chart_and_send, generate_chart_rollback
from log import init_logger
from utils import expired_info, send_error, reorder_gates, is_subnet_or_supernet, match_results, get_reference_bw, display_gates, ping_netflow
from secrets import token_hex
from mt_network import concurrent_find_bw
from database import get_pass
from async_timeout import timeout

import argparse
import asyncio
import opti
import saturacion
import os
import time

path = os.path.dirname(os.path.abspath(__file__))
logger = init_logger('health-monitor', testing_mode=True)
MIN_GBPS = 0.08
EXEC = False


async def main():
    start = time.time()
    logger.info("=== Obteniendo conexiones a DBs")
    conn_prov, conn_monitor, cursor_prov, cursor_monitor = get_databases()
    gates, router_puertos = await get_active_gates(cursor_prov)
    excluded_subnets = get_excluded_subnets(cursor_monitor)
    moved_networks = get_moved_networks(cursor_monitor, conn_monitor)

    # === Consulta el bw actual de las salidas
    result = await concurrent_find_bw(router_puertos, get_pass())  # === Dict parametrizado de bws usado para simular valores
    # result = {
    #     'rointernetuio1:Bundle-Ether105.100': 52.4,
    #     'rointernetuio1:Bundle-Ether95': 15.1,
    #     'routercdn2uio:HundredGigE0/0/0/1': 51.6,
    #     'rointernetuio1:HundredGigE0/0/0/2': 50.9,
    #     'rointernetuio1:Bundle-Ether93': 13.6,
    #     'rointernetuio1:Bundle-Ether90': 9.5,
    #     'rointernetgye4:TenGigE0/0/0/5': 8.3,
    #     'rointernetgye4:Bundle-Ether196': 99.5,
    #     'rointernetgye4:HundredGigE0/2/0/2': 75.5,
    #     'rointernetgye4:Bundle-Ether300': 92.1,
    #     'rointernetgye4:Bundle-Ether252': 39,
    #     'roclientesdcgye1:Bundle-Ether99': 31.6,
    #     'rointernetgye4:Bundle-Ether93': 14,
    #     'rointernetuio1:Bundle-Ether98': 14.4,
    #     'rointernetgye4:Bundle-Ether96': 96.3,
    #     'rointernetuio1:TenGigE0/3/0/1': 0.45,
    #     'rointernetuio1:Bundle-Ether106.50': 0,
    #     'rointernetuio2:100GE0/8/0': 90.2,
    #     'rointernetuio2:Eth-Trunk105.100': 93.2,
    #     'rointernetgye2:Eth-Trunk196': 91.1
    # }
    match_results(gates, result)

    # === Actualiza en la base de datos monitor de salidas e incrementa counters en subredes
    update_db_monitor(gates, cursor_monitor, conn_monitor)
    update_db_subnet_counters(cursor_monitor, conn_monitor)

    # === Sort by load
    dict_gates = gates
    gates, gye_gates, uio_gates = reorder_gates(gates)
    display_gates(gates)

    # === PROCESO DE DESCONGESTION - SATURADAS
    if args.descongestion:
        # === Verificar puertas saturadas
        saturadas = obtener_saturadas(gates)
        if len(saturadas) > 0:
            saturadas = display_saturadas(saturadas)

            # === Escoge la salida saturada mas urgente - Prioridad enlaces de mayor capacidad absoluta
            saturada, reference = obtener_saturada_prioridad(saturadas)

            # === Escoge la mejor salida para descongestionar
            # mejor_salida = saturacion.find_best_gate(saturada, gye_gates, uio_gates, reference)
            mejor_salida = saturacion.find_best_gate(saturada, gates, reference)
            if mejor_salida != "":
                locality = "UIO" if "uio" in saturada.gate else "GYE"
                attributes = saturacion.analyze_attributes(mejor_salida, reference, locality, gates)
                logger.info(mejor_salida)
                for att in attributes:
                    if att['score'] == 5:
                        logger.info(att)
                    elif att['score'] == 1 or att['score'] == 0:
                        logger.error(att)
                    else:
                        logger.warning(att)

                logger.info(f"Mejor salida {mejor_salida.gate} - Load={mejor_salida.load}% - "
                            f"Espacio disponible={round((mejor_salida.capacidad * mejor_salida.threshold / 100) - mejor_salida.current_gbps, 2)} Gbps")

                # === Escoge la mejor subred a mover - Prioridad subredes menores a la capacidad absoluta y cercanas al valor de referencia
                top_networks = find_top_subnets(saturada)
                mejores_subredes, bucket_value, err = find_best_subnets(top_networks, mejor_salida.available, reference, moved_networks.get(saturada.gate, []),
                                                                        excluded_subnets)
                if not err:
                    # === Actualiza en base el status de red que provoco la saturacion
                    update_db_monitor_movement(dict_gates, cursor_monitor, conn_monitor)
                    # === Envia a telegram notificacion
                    generate_chart_and_send(saturada, mejores_subredes, mejor_salida, bucket_value)

                    # === Actualiza las redes como pending en la base de datos
                    for mejor_subred in mejores_subredes:
                        premove_subnet_db(saturada, mejor_subred, mejor_salida, "pending", "saturacion", cursor_monitor, conn_monitor)

        # === PROCESO DE ROLLBACK - SATURADAS
        devolver = find_unlocked_subnets(cursor_monitor)
        if len(devolver) > 0:
            logger.info(f"Se han encontrado {len(devolver)} subredes que pueden volver a su salida original.")
            for salida_actual, subred, salida_original, token in devolver:
                destino = dict_gates[salida_original.gate]

                subred['gbps'], valid_traffic = valid_subnet_traffic(subred['net'], subred['gbps'], subred['recorded_gbps'])
                if valid_traffic:
                    if destino.return_available > subred['gbps']:
                        # === Envia a telegram notificacion
                        generate_chart_rollback(subred, destino, subred['gbps'])
                        premove_subnet_rollback_db(dict_gates[salida_original.gate].current_gbps, dict_gates[salida_actual.gate].current_gbps, subred, token,
                                                   cursor_monitor, conn_monitor)

                        # === Actualiza capacidad disponible en el origen en caso que se mueva la red
                        destino.return_available -= subred['gbps']
                        logger.info(f"Capacidad de retorno disponible en el origen {salida_original.gate} = {round(destino.return_available, 2)}G")
                    else:
                        logger.info(f"No hay capacidad disponible para devolver la red {subred['net']}[{subred['gbps']}G] de {salida_actual.gate} "
                                    f"a su salida original {salida_original.gate} [{dict_gates[salida_original.gate].current_gbps}G]: Return available: {destino.return_available}G")

    # === PROCESO DE OPTIMIZACION - MEJOR COSTO
    if args.greedy:
        logger.info("Iniciando proceso de optimizacion de salidas internacionales de costo variable.")
        optimizable, opt_reference = obtener_optimizables(gates)
        if optimizable != "":
            best_opt_gate = opti.find_best_gate(optimizable, gye_gates, uio_gates)
            if best_opt_gate != "":
                logger.info(f"Mejor salida seleccionada para optimizar: {best_opt_gate}")
                top_opt_net = find_top_subnets(optimizable)
                best_opt_net, bucket_value_opt, err = find_best_subnets(top_opt_net, best_opt_gate.available, opt_reference,
                                                                        moved_networks.get(optimizable.gate, []), excluded_subnets)
                if not err:
                    # === Envia a telegram notificacion
                    # generate_chart_and_send(saturada, mejores_subredes, mejor_salida, bucket_value)

                    # === Actualiza las redes como pending en la base de datos
                    for mejor_subred in best_opt_net:
                        logger.warning(f"RED: {mejor_subred}")
                        premove_subnet_db(optimizable, mejor_subred, best_opt_gate, "pending", "optimizacion", cursor_monitor, conn_monitor)

    if conn_prov:
        conn_prov.close()
    if conn_monitor:
        conn_monitor.close()
    # === TODO crear funcion para updatear logs importantes en la base
    logger.info(f"{round(time.time() - start, 3)} seconds")


# === HELPERS
def valid_subnet_traffic(net, gbps, recorded_bw):
    if gbps == -1:
        if ping_netflow():
            logger.warning(f"Subred {net} no se observa en Netflow, pero Netflow esta activo. Tráfico de subred se asume el de la db {recorded_bw}.")
            return recorded_bw, True
        else:
            logger.warning(f"Netflow no esta activo, verificar en el servidor principal.")
            return 0, False
    else:
        return gbps, True


def obtener_optimizables(gates):
    optimizables = []
    title = 0
    for gate in gates:
        gate.optimal_bw = round(gate.optimal_thold * gate.capacidad / 100, 2)
        if gate.optimal_thold != 100 and gate.current_gbps >= gate.optimal_bw:
            if title == 0:
                logger.warning("{0:40}{1:15}{2:>10}{3:>15}{4:>15}{5:>15}".format("GATE", "PROVIDER", "CAPACITY", "CURRENT BW", "OPTIMAL BW", "OPTIMAL L/T"))
            logger.warning("{0:40}{1:15}{2:>10}{3:>15}{4:>15}{5:>15}".format(gate.gate, gate.proveedor, f"{gate.capacidad}G", f"{gate.current_gbps}Gbps",
                                                                             f"{gate.optimal_bw}Gbps",
                                                                             f"{gate.load}/{gate.optimal_thold} %"))
            if gate.current_gbps >= gate.optimal_bw:
                optimizables.append(gate)
            title += 1
    optimizables = sorted(optimizables, key=lambda item: (item.optimal_priority, (item.current_gbps - item.optimal_bw)), reverse=True)
    if len(optimizables) > 0:
        opt = optimizables[0]
        ref = round((opt.current_gbps - opt.optimal_bw) * 1.1,
                    2)  # === Un 10% mas de lo justo para no tenerlo en el umbral de optimizacion y que dispare a menudo alertas
        logger.info(f"Se optimizara la siguiente salida {opt.gate} ({opt.current_gbps}/{opt.optimal_bw})."
                    f"Prioridad {opt.optimal_priority}")
        logger.info(f"Valor de subred de referencia de optimizacion: {ref}G")
        return optimizables[0], ref
    else:
        return "", None


def obtener_saturada_prioridad(saturadas):
    saturada = saturadas[0]
    logger.info(f"La salida {saturada.gate} se encuentra saturada, se detectaran las subredes a moverse.")
    reference = get_reference_bw(saturada.capacidad)
    logger.info(f"Valor de subred de referencia para interface de {saturada.capacidad}G: {reference}G")
    return saturada, reference


def display_saturadas(saturadas):
    logger.warning(f"Se detecta {len(saturadas)} salidas saturadas")
    saturadas = sorted(saturadas, key=lambda item: item.capacidad, reverse=True)
    logger.warning("{0:40}{1:15}{2:>10}{3:>15}{4:>15}".format("GATE", "PROVIDER", "CAPACITY", "CURRENT BW", "LOAD/THRESHOLD"))
    for gate in saturadas:
        logger.warning("{0:40}{1:15}{2:>10}{3:>15}{4:>15}".format(gate.gate, gate.proveedor, f"{gate.capacidad}G", f"{gate.current_gbps}Gbps",
                                                                  f"{gate.load}/{gate.threshold} %"))
    return saturadas


def obtener_saturadas(gates):
    saturadas = []
    for gate in gates:
        if gate.load >= gate.threshold:
            saturadas.append(gate)
    return saturadas


# === STATUS pending->commit->rollback->pending-rollback->finished
def premove_subnet_rollback_db(original_gate_bw, actual_gate_bw, prefix, token, cursor, conn):
    logger.info(f"Registrando retorno de subred {prefix} como proceso pendiente")
    sql = f"UPDATE moved_prefixes SET status='pending-rollback',origin_bw_at='{original_gate_bw}',destination_bw_at='{actual_gate_bw}',subnet_bw_at='{prefix['gbps']}' WHERE token='{token}'"
    cursor.execute(sql)
    conn.commit()


def premove_subnet_db(salida_origen, subred, salida_destino, status, module, cursor, conn):
    logger.info(f"Registrando subred {subred['net']} en la base de datos como proceso pendiente.")
    sql = f"INSERT INTO moved_prefixes(prefix,from_router,from_port,to_router,to_port,origin_bw_at,subnet_bw_at,destination_bw_at,status,token,module) VALUES ('{subred['net']}','{salida_origen.router}','{salida_origen.name}','{salida_destino.router}','{salida_destino.name}','{salida_origen.current_gbps}','{subred['gbps']}','{salida_destino.current_gbps}','{status}','{token_hex(4)}','{module}')"
    cursor.execute(sql)
    conn.commit()


def find_best_subnets(networks, available, reference, moved_networks, excluded):
    logger.info("Seleccionando la mejor subred o subredes a mover para descongestionar.")
    bucket = []
    bucket_value = 0

    networks = sorted(networks, key=lambda item: item['bps'], reverse=True)
    candidates = []
    for net in networks:
        gbps = round(net['bps'] / 1000_000_000, 2)
        # === Eliminar redes menores a MIN_GBPS o mayores a available o excluidas
        if MIN_GBPS <= gbps <= available and not expired_info(net) and net['net'] not in excluded:
            if net['net'] not in moved_networks:
                net["score"] = round((reference - gbps) ** 2, 2)
                net["gbps"] = gbps
                net["mask"] = int(net["net"].split("/")[1])
                candidates.append(net)
            else:
                logger.warning(f"Red {net['net']} ya fue movida de esta salida segun la base de datos. Por favor revisar por qué aparece en esta salida.")
        elif gbps < MIN_GBPS:
            logger.warning(f"Red {net['net']} - {gbps}G tiene menor BW que el minimo = {MIN_GBPS}G.")
        elif gbps > available:
            logger.warning(f"Red {net['net']} - {gbps}G tiene mayor bw que el bw disponible = {available}G")
        elif expired_info(net):
            logger.warning(f"Red {net['net']} tiene informacion expirada de Netflow.")
        elif net['net'] in excluded:
            logger.warning(f"Red {net['net']} se encuentra entre las redes excluidas.")
    # === Valor negativo permite ordernar por la mascara mas especifica y el menor score
    candidates = sorted(candidates, key=lambda item: (-item['mask'], item['score']))
    for c in candidates:
        logger.warning(f"RAW: {c}")

    if len(candidates) > 0:
        # === Agrega la subred mas cercana al valor de referencia y la quita de las candidatas
        bucket.append(candidates[0])
        bucket_value += candidates[0]['gbps']
        candidates.pop(0)
        new_reference = reference - bucket_value

        for i in range(len(candidates)):
            another_subnet, err = iterative_find_best_subnet(bucket, candidates, new_reference)
            if err:
                if err == "es supernet":
                    candidates.pop(candidates.index(another_subnet))
                else:
                    logger.warning(err)
                    break
            else:
                if bucket_value + another_subnet['gbps'] > available or bucket_value + another_subnet['gbps'] > reference:
                    logger.warning(f"Red {another_subnet['net']} excede el valor disponible o referencia")
                    candidates.pop(candidates.index(another_subnet))
                else:
                    bucket_value += another_subnet['gbps']
                    bucket.append(another_subnet)
                    candidates.pop(candidates.index(another_subnet))
                    new_reference = reference - bucket_value

        logger.info(f"Se ha agrupado {len(bucket)} subredes, sumando un total de {round(bucket_value, 2)}Gbps a mover.")
        return bucket, bucket_value, None
    else:
        logger.error("No se pudo encontrar una red adecuada para mover, por favor revisar los logs.")
        return None, None, "No se pudo encontrar una red adecuada para mover, por favor revisar los logs."


def iterative_find_best_subnet(bucket, candidates, reference):
    if len(candidates) > 0:
        for net in candidates:
            net["score"] = round((reference - net['gbps']) ** 2, 2)
        candidates = sorted(candidates, key=lambda item: (-item['mask'], item['score']))
        if not (is_subnet_or_supernet(candidates[0], bucket)):
            return candidates[0], None
        else:
            return candidates[0], "es supernet"
    else:
        return None, "No existen mas subredes para agregar al bucket"


# === SYSTEM EXECUTION
async def main_wrapper():
    async with timeout(270):
        await main()


parser = argparse.ArgumentParser(description="Script para analizar las salidas internacionales y mover redes a un canal de backup.")
parser.add_argument("--dry-run", action="store_true", help="Solo muestra las redes a mover y la configuracion a ejecutar.")
parser.add_argument("--greedy", action="store_true", help="Habilita el modulo de optimizacion de salidas de costo variable.")
parser.add_argument("--descongestion", action="store_true", help="Habilita el modulo de descongestion.")
args = parser.parse_args()

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main_wrapper())
        loop.close()
    except asyncio.TimeoutError:
        send_error("La aplicacion ha finalizado por timeout, por favor consultar con NetDev.")
    except Exception as e:
        logger.exception(e)
        send_error("Ocurrio un error al ejecutar main, por favor consultar con NetDev.")
