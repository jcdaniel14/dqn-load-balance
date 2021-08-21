import subprocess
import asyncio
import concurrent.futures
import logging

logger = logging.getLogger("health-monitor")
logger.setLevel(logging.INFO)

WORKERS = 32


async def concurrent_snmp_query(gates):
    logger.info(f"Consultando capacidad de enlaces via SNMP")
    snmp_capacity, snmp_ids, entire_status = {}, {}, {}
    snmp_ids = dict()
    unique_routers = get_unique_routers(gates)
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as executor:
        futures = [get_high_speed_thread(executor, router) for router in unique_routers]
        for i, future in enumerate(asyncio.as_completed(futures)):
            result, ids, status = await future
            snmp_capacity.update(result)
            snmp_ids.update(ids)
            entire_status.update(status)

    return snmp_capacity, snmp_ids, entire_status


async def get_high_speed_thread(executor, router):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_high_speed, router)


def get_high_speed(router):
    my_dict = {}
    snmp_ids_to_name, port_to_id = get_snmp_ids(router)
    ids_to_speed = get_speed(router)
    for snmp_id, speed in ids_to_speed.items():
        if snmp_id in snmp_ids_to_name:
            my_dict[f"{router}:{snmp_ids_to_name[snmp_id]}"] = int(speed) / 1000  # === Speed en Gbps

    status = get_status(router, snmp_ids_to_name)
    return my_dict, port_to_id, status


def get_snmp_ids(router) -> dict:
    snmp_ids = {}
    port_to_id = {}
    try:
        cmd = f"snmpwalk -v 2c -c 8JGptmp3T9c {router} ifName"
        output = subprocess.run([cmd], stdout=subprocess.PIPE, shell=True).stdout.decode("utf-8")
        for line in output.split("\n"):
            words = line.strip().split()
            if "ifName" in line and "." in line:
                snmp_ids[words[0].split(".")[1]] = words[-1]
                port_to_id[f"{router}:{words[-1]}"] = words[0].split(".")[1]
    except Exception:
        raise Exception(f"No se pudo identificar el ID SNMP de puerto del {router} mediante SNMP.")
    return snmp_ids, port_to_id


def get_status(router, snmp_ids) -> dict:
    status = {}
    try:
        cmd = f"snmpwalk -v 2c -c 8JGptmp3T9c {router} ifAdminStatus"
        output = subprocess.run([cmd], stdout=subprocess.PIPE, shell=True).stdout.decode("utf-8")
        for line in output.split("\n"):
            words = line.strip().split()
            if "ifAdminStatus" in line and "." in line:
                tmp = words[-1]
                snmp_id = words[0].split(".")[1]
                if "up" in tmp:
                    status[f"{router}:{snmp_ids.get(snmp_id,'')}"] = "up"
                else:
                    status[f"{router}:{snmp_ids.get(snmp_id, '')}"] = "down"
    except Exception:
        raise Exception(f"No se pudo identificar el status de interfaces del {router} mediante SNMP.")
    return status


def get_speed(router) -> dict:
    speed = {}
    try:
        cmd = f"snmpwalk -v 2c -c 8JGptmp3T9c {router} ifHighSpeed"
        output = subprocess.run([cmd], stdout=subprocess.PIPE, shell=True).stdout.decode("utf-8")
        for line in output.split("\n"):
            words = line.strip().split()
            if "ifHighSpeed" in line and "." in line:
                speed[words[0].split(".")[1]] = words[-1]
    except Exception:
        raise Exception(f"No se pudo identificar la capacidad del {router} mediante SNMP.")
    return speed


def get_unique_routers(gates):
    routers = []
    for gate in gates:
        router = gate.split(":")[0]
        if router not in routers:
            routers.append(router)
    return routers
