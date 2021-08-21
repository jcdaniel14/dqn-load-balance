from database import get_mysql_db
from netaddr import IPAddress, IPNetwork
from datetime import datetime as dt

from log import init_logger

logger = init_logger('test-auto', file=False)

MIN_GBPS = 0.1


def expired_info(net):
    net_ts = dt.strptime(net['ts'], "%Y-%m-%d %H:%M:%S")
    now_ts = dt.now()

    delta = now_ts - net_ts
    minutes = round(delta.total_seconds() / 60, 2)
    return minutes < 20


def is_subnet_or_supernet(candidate, bucket):
    for b in bucket:
        if IPAddress(b["net"].split("/")[0]) in IPNetwork(candidate["net"]):
            return True
        elif IPAddress(candidate["net"].split("/")[0]) in IPNetwork(b["net"]):
            return True
    return False


def iterative_find_best_subnet(bucket, candidates, reference):
    if len(candidates) > 0:
        for net in candidates:
            net["score"] = round((reference - net['gbps']) ** 2, 2)
        candidates = sorted(candidates, key=lambda item: (item['score'], -item['mask']))
        if not (is_subnet_or_supernet(candidates[0], bucket)):
            return candidates[0], None
        else:
            return candidates[0], "es supernet"
    else:
        return None, "No existen mas subredes para agregar al bucket"


def find_best_subnets(networks, available, reference, moved_networks, excluded):
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
            if net['net'] in excluded:
                logger.warning(f"Ignorando red {net['net']} debido a que se encuentra excluida")
            elif MIN_GBPS <= gbps:
                logger.warning(f"Ignorando red {net['net']} debido a que tiene un BW menor a 100Mbps")
    # === Valor negativo permite ordernar por la mascara mas especifica y el menor score
    candidates = sorted(candidates, key=lambda item: (-item['mask'], item['score']))

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
                    break
            else:
                if bucket_value + another_subnet['gbps'] > available or bucket_value + another_subnet['gbps'] > reference:
                    candidates.pop(candidates.index(another_subnet))
                else:
                    bucket_value += another_subnet['gbps']
                    bucket.append(another_subnet)
                    candidates.pop(candidates.index(another_subnet))
                    new_reference = reference - bucket_value

        return bucket, None
    else:
        return None, "No se pudo encontrar una red adecuada para mover, por favor revisar los logs."


def get_excluded_subnets():
    conn = get_mysql_db(db='monitor')
    cursor = conn.cursor()
    prefixes = []
    sql = "SELECT prefix FROM exclusiones"
    cursor.execute(sql)
    for row in cursor.fetchall():
        prefixes.append(row[0])
    if conn:
        conn.close()
    return prefixes


def test_best_subnet_1():
    logger.info("Probando solo con redes de Telia DDoS - Tratando de liberar 10G")
    top_networks = [
        {'net': '200.93.220.0/24', 'bps': 6067289244.444446, 'ts': '2021-02-03 09:36:00'},
        {'net': '186.101.29.0/24', 'bps': 3468907155.555556, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.39.55.0/24', 'bps': 2241782799.9999995, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.198.41.0/24', 'bps': 2241782799.9999995, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.198.10.0/24', 'bps': 62497377.77777778, 'ts': '2021-02-03 09:36:00'}]
    excluded_subnets = get_excluded_subnets()
    chosen_bucket, err = find_best_subnets(top_networks, 10, 10, [], excluded_subnets)
    logger.info(err)
    assert chosen_bucket is None
    if chosen_bucket:
        logger.info(f"Redes seleccionadas para mover: {len(chosen_bucket)}")
    else:
        logger.info(f"Redes seleccionadas para mover: 0")


def test_best_subnet_2():
    logger.info("Probando con redes de Telia DDoS y redes CGNAT - Tratando de liberar 10G")
    top_networks = [
        {'net': '200.93.220.0/24', 'bps': 6067289244.444446, 'ts': '2021-02-03 09:36:00'},
        {'net': '186.101.29.0/24', 'bps': 3468907155.555556, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.39.55.0/24', 'bps': 2241782799.9999995, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.198.41.0/24', 'bps': 2241782799.9999995, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.198.10.0/24', 'bps': 62497377.77777778, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.32.0/19', 'bps': 6067289244.444446, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.62.0/24', 'bps': 3468907155.555556, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.59.0/24', 'bps': 2241782799.9999995, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.56.0/23', 'bps': 83915422.22222222, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.55.0/24', 'bps': 62497377.77777778, 'ts': '2021-02-03 09:36:00'}]
    excluded_subnets = get_excluded_subnets()
    chosen_bucket, err = find_best_subnets(top_networks, 10, 10, [], excluded_subnets)

    assert chosen_bucket is not None
    logger.info(f"Redes seleccionadas para mover: {len(chosen_bucket)}")
    for b in chosen_bucket:
        logger.info(f"{b['net']} = {b['gbps']}G")


def test_best_subnet_3():
    logger.info("Probando solo con redes CGNAT/Telconet - Tratando de liberar 10G")
    top_networks = [
        {'net': '181.199.32.0/19', 'bps': 6067289244.444446, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.62.0/24', 'bps': 3468907155.555556, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.59.0/24', 'bps': 2241782799.9999995, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.58.0/23', 'bps': 2241782799.9999995, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.54.0/24', 'bps': 210186488.88888887, 'ts': '2021-02-03 09:36:00'},
        {'net': '200.110.64.0/19', 'bps': 99458177.77777778, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.56.0/24', 'bps': 83915422.22222222, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.56.0/23', 'bps': 83915422.22222222, 'ts': '2021-02-03 09:36:00'},
        {'net': '181.199.55.0/24', 'bps': 62497377.77777778, 'ts': '2021-02-03 09:36:00'},
        {'net': '64.46.64.0/19', 'bps': 33430711.11111111, 'ts': '2021-02-03 09:36:00'},
        {'net': '8.242.218.0/24', 'bps': 755955.5555555555, 'ts': '2021-02-03 09:36:00'},
        {'net': '69.65.128.0/19', 'bps': 369022.22222222225, 'ts': '2021-02-03 09:36:00'}]
    excluded_subnets = get_excluded_subnets()
    chosen_bucket, err = find_best_subnets(top_networks, 10, 10, [], excluded_subnets)

    assert chosen_bucket is not None
    logger.info(f"Redes seleccionadas para mover: {len(chosen_bucket)}")
    for b in chosen_bucket:
        logger.info(f"{b['net']} = {b['gbps']}G")
