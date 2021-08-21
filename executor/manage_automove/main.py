from database import get_mysql_db, get_pass
from log import init_logger
from async_timeout import timeout
from loader import get_prefixes_from_db, send_error, handle_session, advertised_route
from utils import reduced_port, edit_prefix

import argparse
import asyncio
import json
import sys

logger = init_logger('auto-move')


# === MAIN
async def main():
    if args.option == "show":
        prefixes = get_prefixes_from_db()
        print(json.dumps({'status': 'ok', 'response': prefixes}))
    elif args.option == "exec":
        logger.info(f"Ejecutando movimiento de red registrado en MySQL como {args.token}")
        await move_network(args.token)
    else:
        send_error("La opcion indicada no existe, por favor revisar con NetDev.")


# === SYSTEM EXECUTION
async def move_network(token):
    prefix, origin_router, origin_port, destination_router, destination_port, status = "", "", "", "", "", ""
    try:
        pwd = get_pass()
        conn = get_mysql_db(db="monitor")
        cursor = conn.cursor()
        conn_p = get_mysql_db(db='proveedores')
        cursor_proveedor = conn_p.cursor()
        sql = f"SELECT prefix, from_router, from_port, to_router, to_port, status FROM moved_prefixes WHERE token='{token}' AND status IN ('pending','pending-rollback')"
        cursor.execute(sql)
        for row in cursor.fetchall():
            prefix = row[0]
            origin_router = row[1]
            origin_port = row[2]
            destination_router = row[3]
            destination_port = row[4]
            status = row[5]

        origin_os = find_os_in_db(origin_router, cursor_proveedor)
        destination_os = find_os_in_db(destination_router, cursor_proveedor)

        # === Crea sesiones a ambos routers
        origin = handle_session(origin_router, pwd)
        dest = handle_session(destination_router, pwd)
        if not origin:
            send_error(f"No se pudo conectar por SSH a {origin_router}, por favor consultar con NetDev.")
        if not dest:
            send_error(f"No se pudo conectar por SSH a {destination_router}, por favor consultar con NetDev.")

        # === Ejecuta la insercion de la prefix
        if status == 'pending':
            logger.info("Status: pending -- Anunciando en destino")
            edit_prefix(f"NETDEV-ANUNCIO_AUTO_{reduced_port(destination_port)}", "add", prefix, destination_os, dest)

            strikes = 0
            while not advertised_route(destination_port, prefix, destination_os, dest, cursor_proveedor):
                logger.info("No se observa la red en las advertised-routes, reintentando en 10 segundos.")
                await asyncio.sleep(10)
                strikes += 1
                if strikes >= 3:
                    break

            if strikes >= 3:
                send_error(
                    f"No se observa la red {prefix} entre las advertised-routes del destino ({destination_router}:{destination_port}), por lo que no se continuara con el bloqueo de la prefix. Por favor revisar con Networking.")
            else:
                logger.info("Status: pending -- Bloqueando en origen")
                edit_prefix(f"NETDEV-BLOQUEO_AUTO_{reduced_port(origin_port)}", "add", prefix, origin_os, origin)
        elif status == 'pending-rollback':
            logger.info("Status: pending-rollback -- Quitando bloqueo en origen")
            edit_prefix(f"NETDEV-BLOQUEO_AUTO_{reduced_port(origin_port)}", "remove", prefix, origin_os, origin)

            strikes = 0
            while not advertised_route(origin_port, prefix, origin_os, origin, cursor_proveedor):
                logger.info("No se observa la red en las advertised-routes, reintentando en 10 segundos.")
                await asyncio.sleep(10)
                strikes += 1
                if strikes >= 3:
                    break

            if strikes >= 3:
                send_error(
                    f"No se observa la red {prefix} entre las advertised-routes de la salida original ({origin_router}:{origin_port}), por lo que no se quitara el anuncio de la prefix. Por favor revisar con Networking.")

            logger.info("Status: pending-rollback -- Quitando anuncio en destino")
            edit_prefix(f"NETDEV-ANUNCIO_AUTO_{reduced_port(destination_port)}", "remove", prefix, destination_os, dest)

        origin.disconnect()
        dest.disconnect()
        set_db_status(token, status, cursor, conn)
        if conn:
            conn.close()
        if conn_p:
            conn_p.close()
        print(json.dumps({'status': 'ok', 'response': f'Se ha realizado el movimiento de la red {prefix} correctamente.'}))
        sys.exit(0)
    except Exception as e:
        logger.exception(e)
        send_error("Ocurrio un error al extraer la red de la base de datos, por favor consultar con NetDev.")
    send_error("Ocurrio un error al extraer la red de la base de datos, por favor consultar con NetDev.")


def set_db_status(token, status, cursor, conn):
    logger.info("Actualizando status en la base de datos")
    if status == "pending":
        sql = f"UPDATE moved_prefixes SET status='commit' WHERE status='{status}' AND token='{token}'"
        cursor.execute(sql)
        conn.commit()
    elif status == "pending-rollback":
        sql = f"UPDATE moved_prefixes SET status='finished' WHERE status='{status}' AND token='{token}'"
        cursor.execute(sql)
        conn.commit()


def find_os_in_db(router, cursor) -> int:
    try:
        sql = f"SELECT os_type FROM proveedor WHERE router = '{router}' AND enabled=1 LIMIT 1"
        cursor.execute(sql)
        os = cursor.fetchone()
        return int(os[0])
    except Exception as e:
        logger.exception(e)
    return 5


async def main_wrapper():
    async with timeout(270):
        await main()


parser = argparse.ArgumentParser(
    description="Script para mostrar movimientos de redes de la DB, y ejecutar configuracion de movimientos de red de acuerdo a la DB.")
parser.add_argument("--option", default="show", help="Escoje la opcion a ejecutar (show/execute)")
parser.add_argument("--token", default="", help="Token de la red a mover.")
parser.add_argument("--dry-run", action="store_true", help="No ejecuta configuracion.")  # Boolean
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
