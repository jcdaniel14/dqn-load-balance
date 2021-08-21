from log import init_logger
import subprocess
import json


logger = init_logger('test-auto', file=False)


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


def test_netflow_alive():
    assert ping_netflow() is True
