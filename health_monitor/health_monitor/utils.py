from netaddr import IPAddress, IPNetwork
from datetime import datetime as dt
import subprocess
import logging
import sys
import json

logger = logging.getLogger("health-monitor")
logger.setLevel(logging.INFO)
SAFEGUARD = 0.9  # === 90% del valor de referencia se mueve para dar margen y no saturar otra salida al mover una red.


def get_reference_bw(capacidad):
    if 0 <= capacidad <= 10:
        return 2 * SAFEGUARD
    elif 10 < capacidad <= 60:
        return 6 * SAFEGUARD
    elif 60 < capacidad <= 100:
        return 11.11 * SAFEGUARD
    else:
        return 2 * SAFEGUARD


def expired_info(net):
    net_ts = dt.strptime(net['ts'], "%Y-%m-%d %H:%M:%S")
    now_ts = dt.now()

    # === Compara si la info de subnet es mayor a 30 minutos la rechaza TODO activar validacion de minutos
    delta = now_ts - net_ts
    minutes = round(delta.total_seconds() / 60, 2)
    expired = minutes > 30
    if expired:
        logger.warning(f"Expired time: {net_ts} - Local time: {now_ts}")
    return expired


def ping_netflow() -> bool:
    logger.info("Verificando si netflow esta activo")
    cmd = "/home/gsantiago/go_2020/netflow/internet_status/internet_status"
    logger.info(cmd)
    output = subprocess.run([cmd], stdout=subprocess.PIPE, shell=True).stdout.decode("utf-8")
    if output.find("{") == -1:
        return False
    output = output[output.find("{"):].strip().strip("\n")
    rs = json.loads(output)

    for item in rs["response"]:
        gate = f"{item['exporter']}:{item['name']}"
        if item['currentTraffic'] != 0:
            logger.info(f"Se detecta netflow activo, con registros de {gate} = {item['currentTraffic']}")
            return True
    return False


def locked_subnet(ts):
    now_ts = dt.now()

    # === Compara si la subred se actualizo o movio hace menos de 30 minutos no es valida
    delta = now_ts - ts
    minutes = round(delta.total_seconds() / 60, 2)
    return minutes < 30


def reduced_port(port):
    port = port.replace("/", "_")
    if "." in port:
        port = port.split(".")[0]

    if port.startswith("Bundle-Ether"):
        return port.replace("Bundle-Ether", "BE")
    elif port.startswith("TenGigE"):
        return port.replace("TenGigE", "Te")
    elif port.startswith("HundredGigE"):
        return port.replace("HundredGigE", "Hu")
    return port


def is_subnet_or_supernet(candidate, bucket):
    for b in bucket:
        if IPAddress(b["net"].split("/")[0]) in IPNetwork(candidate["net"]):
            logger.warning(f"{candidate['net']} contiene a la red seleccionada {b['net']}")
            return True
        elif IPAddress(candidate["net"].split("/")[0]) in IPNetwork(b["net"]):
            logger.warning(f"{candidate['net']} es subnet de {b['net']}")
            return True
    return False


def reorder_gates(gates):
    gates = sorted(gates.values(), key=lambda item: (item.optimal_available, -item.optimal_priority, item.available), reverse=True)

    gye, uio = [], []
    for gate in gates:
        if "uio" in gate.gate:
            uio.append(gate)
        else:
            gye.append(gate)
    return gates, gye, uio


def display_gates(gates):
    logger.info(
        "{0:40}{1:15}{2:>10}{3:>15}{4:>15}{5:>15}{6:>15}{7:>10}".format("GATE", "PROVIDER", "CAPACITY", "CURRENT BW", "AVAILABLE", "LOAD/THRESHOLD", "OPTIMAL",
                                                                        "PRIORITY"))
    for gate in gates:
        logger.info("{0:40}{1:15}{2:>10}{3:>15}{4:>15}{5:>15}{6:>15}{7:>10}".format(gate.gate, gate.proveedor, f"{gate.capacidad}G", f"{gate.current_gbps}Gbps",
                                                                                    f"{gate.available}Gbps",
                                                                                    f"{gate.load}/{gate.threshold} %",
                                                                                    f"{gate.optimal_available}Gbps",
                                                                                    gate.optimal_priority))


def match_results(gates, result):
    for gate, current_bw in result.items():
        if gate in gates:
            gates[gate].current_gbps = current_bw
            gates[gate].load = round(100 * gates[gate].current_gbps / gates[gate].capacidad, 2)
            gates[gate].calculate_available()
    return


def send_error(msg):
    rs = {"status": "error", "error": msg}
    print(json.dumps(rs))
    sys.exit(0)
