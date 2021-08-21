from netaddr import IPNetwork, AddrFormatError
from devnet_ssh import SSHConnect
from database import get_mysql_db
from datetime import datetime as dt
from paramiko import AuthenticationException, SSHException

import socket
import json
import sys
import logging

logger = logging.getLogger("auto-move")
HUAWEI = 3
IOSXR = 5


def handle_session(device, pwd):
    try:
        session = SSHConnect(host=device, user="automatico", pwd=pwd)
        if session.is_connected():
            return session
    except AuthenticationException as e:
        logger.warning(f"[{device}] Password: {e}")
    except SSHException as e:
        logger.warning(f"[{device}] SSH: {e}")
    except socket.timeout as e:
        logger.warning(f"[{device}] Timeout: {e}")
    except socket.gaierror as e:
        logger.warning(f"[{device}] DNS Resolution: {e}")
    except Exception as e:
        logger.exception(f"[{device}] Unknown: {e}")
    return None


def advertised_route(port, prefix, os_type, session, cursor):
    peer_v4 = get_peer_from_db(port, session.host, cursor)
    if peer_v4 == "":
        send_error(f"No se pudo determinar el peer IPv4 de la salida {session.host}:{port}")
    advertised_prefixes = get_advertised_prefixes(peer_v4, os_type, session)
    return prefix in advertised_prefixes


def get_advertised_prefixes(peer, os_type, session):
    logger.info(f"Obteniendo los prefijos anunciados a {peer}.")
    prefixes = []
    if os_type == HUAWEI:
        cmd = f"display bgp vpnv4 vpn-instance telconet routing-table peer {peer} advertised-routes"
    else:
        cmd = f"sh bgp vrf telconet neighbor {peer} advertised-routes"
    logger.info(cmd)
    for line in session.send_command(cmd):
        words = line.strip().split()
        if os_type == HUAWEI:
            if len(words) >= 2:
                if is_network(words[1]):
                    prefixes.append(words[1])
        else:
            if is_network(words[0]):
                prefixes.append(words[0])
    logger.info(f"Se han encontrado {len(prefixes)} prefijos anunciados")
    return prefixes


def get_peer_from_db(port, router, cursor):
    peer = ""
    sql = f"SELECT peer_v4 FROM proveedor WHERE puerto='{port}' AND router='{router}' AND enabled=1"
    cursor.execute(sql)
    row = cursor.fetchone()
    if row:
        peer = row[0]
    return peer


def is_network(network):
    # === Detecta si es Subred, con mascara CIDR
    try:
        IPNetwork(network).is_private()
        return True
    except AddrFormatError:
        return False
    except Exception as e:
        logger.exception(e)
        return False


def get_prefixes_from_db():
    prefixes = []
    try:
        conn = get_mysql_db(db="monitor")
        cursor = conn.cursor()
        sql = "SELECT from_router,from_port,prefix,to_router,to_port,origin_bw_at,subnet_bw_at,destination_bw_at,timestamp,status,token FROM moved_prefixes"
        cursor.execute(sql)
        for row in cursor.fetchall():
            prefixes.append({'origin': f"{row[0]}:{row[1]}", 'prefix': row[2], 'destination': f"{row[3]}:{row[4]}", "origin_bw": row[5], "subnet_bw": row[6],
                             "destination_bw": row[7],
                             'timestamp': dt.strftime(row[8], "%Y-%m-%d %H:%M:%S"), 'status': row[9], 'token': row[10]})
    except Exception as e:
        logger.exception(e)
        send_error("Ha ocurrido un error al conectar con la base de datos MySQL. Por favor revisar con NetDev.")
    return prefixes


def send_error(msg):
    rs = {"status": "error", "error": msg}
    print(json.dumps(rs))
    sys.exit(0)
