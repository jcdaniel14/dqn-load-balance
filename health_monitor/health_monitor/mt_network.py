from devnet_ssh import SSHConnect

import re
import asyncio
import concurrent.futures
import logging

logger = logging.getLogger("health-monitor")
logger.setLevel(logging.INFO)

WORKERS = 8
HUAWEI = 3


async def concurrent_find_bw(router_puertos, pwd):
    logger.info(f"Consultando consumo actual via SSH")
    consumo = {}
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as executor:
        futures = [find_bw_thread(executor, router, stats, pwd) for router, stats in router_puertos.items()]
        for i, future in enumerate(asyncio.as_completed(futures)):
            result = await future
            consumo.update(result)
    return consumo


async def find_bw_thread(executor, router, stats, pwd):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, find_bw, router, stats, pwd)


def find_bw(host, stats, pwd):
    d = {}
    session = SSHConnect.handle_session(host, pwd)
    if session:
        # session = SSHConnect(host=host, user='automatico', pwd=pwd)
        if stats['os_type'] == HUAWEI:
            logger.info(f"Huawei device {host}")
            for port in stats['puertos']:
                result = find_hw_bw(host, port, session)
                d.update(result)
        else:
            batch = []
            for port in stats['puertos']:
                batch.append(port)
                if len(batch) == 5:
                    d.update(find_batch_bw(batch, session))
                    batch = []

            if len(batch) < 5:
                d.update(find_batch_bw(batch, session))
        session.disconnect()
    else:
        logger.warning(f"No se pudo conectar al dispositivo {host} para identificar el bw de puertos")
    return d


def find_hw_bw(host, port, session):
    cmd = f"display interface {port} | i input"
    try:
        for line in session.send_command(cmd):
            if "input rate" in line:
                temp = line.split("bits/sec")[0]
                return {f'{host}:{port}': to_gb(temp.split()[-1])}
    except Exception as e:
        logger.exception(e)
    logger.warning(f"No se pudo detectar el bw en HUAWEI {host}:{port}")
    return {f'{host}:{port}': 0}


def find_batch_bw(puertos, session):
    console = monitor_interfaces(puertos, session)
    block = False
    d = {}

    for line in console:
        line = escape_ansi(line).strip()
        if line != "":
            words = line.strip().split()
            if line.startswith("Interface"):
                block = True
                continue
            elif line.startswith("Quit"):
                block = False
            if len(words) > 1:
                if block:
                    if words[0] != "BE4":
                        d[f"{session.host}:{expand_port(words[0])}"] = format_bw(words[1])
    return d


def monitor_interfaces(puertos, session):
    session.rcv_timeout = 1
    inline_puertos = ""
    for p in puertos:
        inline_puertos += f"{p} "
    if len(puertos) == 1:
        cmd = f"monitor int BE4 {inline_puertos}"
    else:
        cmd = f"monitor int {inline_puertos}"

    try:
        console = session.send_command(cmd, watch_timeout=True)
    except Exception:
        session.send_command("q")
        session.rcv_timeout = 60
        return session.expired_console


def to_gb(bps):
    return round(int(bps) / 1000_000_000, 2)


def expand_port(port):
    if port.startswith("BE"):
        return port.replace("BE", "Bundle-Ether")
    elif port.startswith("Te") and not port.startswith("TenGigE"):
        return port.replace("Te", "TenGigE")
    elif port.startswith("Hu") and not port.startswith("HundredGigE"):
        return port.replace("Hu", "HundredGigE")
    return port


def format_bw(word) -> float:
    word = word.lower().replace("/", "")
    if "g" in word:
        return round(float(word.replace("g", "")), 2)
    elif "m" in word:
        return round(float(word.replace("m", "")) / 1000, 2)
    elif "k" in word:
        return round(float(word.replace("k", "")) / 1000_000, 2)
    else:
        return round(float(word) / 1000_000_000, 2)


def escape_ansi(line):
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)
