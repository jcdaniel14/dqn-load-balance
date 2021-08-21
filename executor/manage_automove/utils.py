from netaddr import IPAddress, AddrFormatError
import logging

logger = logging.getLogger('auto-move')
HUAWEI = 3


def edit_prefix(prefix_set, option, prefix, os_type, session):
    if os_type == HUAWEI:
        actual_prefixes = get_actual_prefixes(prefix_set, session)
        conf = ["system", f"xpl ip-prefix-list {prefix_set}"]
        if option == "add":
            for px in actual_prefixes:
                conf.append(f"{px},")
            tmp = prefix.split('/')
            conf.append(f"{tmp[0]} {tmp[1]}")
            conf.append("end-list")
            conf.append("commit")
            conf.append("return")
        elif option == "remove":
            inline_px = f"{prefix.split('/')[0]} {prefix.split('/')[1]}".strip()
            curated_prefixes = get_curated_prefixes(inline_px, actual_prefixes)
            if len(curated_prefixes) == 0:
                curated_prefixes = ["192.168.1.1 32"]

            for idx, px in enumerate(curated_prefixes):
                if idx == (len(curated_prefixes) - 1):
                    conf.append(px)
                else:
                    conf.append(f"{px},")

            conf.append("end-list")
            conf.append("commit")
            conf.append("return")

        for line in conf:
            logger.info(f"[{session.host}] >> {line}")
            logger.info(f"[{session.host}] << {session.send_command(line)}")
    else:
        cmd1 = f"edit prefix-set {prefix_set} inline {option} {prefix}"
        logger.info(f"[{session.host}] >> {cmd1}")
        logger.info(f"[{session.host}] << {session.send_command(cmd1, expect=']:')}",)
        logger.info(f"[{session.host}] >> yes")
        logger.info(f"[{session.host}] << {session.send_command('yes')}")


def get_curated_prefixes(inline_prefix, prefixes):
    pxs = []
    for px in prefixes:
        px = px.replace(",", "").strip()
        if px == inline_prefix:
            logger.warning(f"Prefix {inline_prefix} detectado, eliminando")
        else:
            pxs.append(px)
    return pxs


def get_actual_prefixes(prefix_set, session):
    pxs = []
    cmd = f"display current config xpl-pfx {prefix_set}"
    for line in session.send_command(cmd):
        line = line.replace(",", "")
        words = line.strip().split()
        if is_ip(words[0]):
            if len(words) >= 2:
                pxs.append(f"{words[0]} {words[1]}")
            else:
                pxs.append(f"{words[0]} 32")
    return pxs


def reduced_port(port):
    port = port.replace("/", "_")
    if "." in port:
        port = port.split(".")[0]

    if port.startswith("Bundle-Ether"):
        return port.replace("Bundle-Ether", "BE")
    elif port.startswith("Eth-Trunk"):
        return port.replace("Eth-Trunk", "BE")
    elif port.startswith("TenGigE"):
        return port.replace("TenGigE", "Te")
    elif port.startswith("HundredGigE"):
        return port.replace("HundredGigE", "Hu")
    elif port.startswith("100GE"):
        return port.replace("100GE", "Hu")
    return port


def is_ip(ip):
    # === Detecta si es IP
    try:
        IPAddress(ip).is_unicast()
        return True
    except AddrFormatError:
        return False
    except Exception as e:
        logger.exception(e)
        return False
