import asyncio
import pytest
import sys

sys.path.append('/home/gsantiago/2021/app/netflow/health_monitor/health_monitor')

from loader import get_databases,get_active_gates
from utils import reorder_gates, display_gates, match_results, get_reference_bw
from saturacion import find_best_gate, analyze_attributes
from log import init_logger


logger = init_logger('test-auto', file=False)


@pytest.mark.asyncio
async def test_best():
    logger.info("Probando eleccion de mejor salida")
    conn_prov, conn_monitor, cursor_prov, cursor_monitor = get_databases()
    gates, router_puertos = await get_active_gates(cursor_prov)
    # result = await concurrent_find_bw(router_puertos, get_pass())  # === Dict parametrizado de bws usado para simular valores
    result = {
        'rointernetuio1:Bundle-Ether105.100': 52.4,
        'rointernetuio1:Bundle-Ether95': 15.1,
        'routercdn2uio:HundredGigE0/0/0/1': 51.6,
        'rointernetuio1:HundredGigE0/0/0/2': 50.9,
        'rointernetuio1:Bundle-Ether93': 13.6,
        'rointernetuio1:Bundle-Ether90': 9.5,
        'rointernetgye4:TenGigE0/0/0/5': 9.3,
        'rointernetgye4:Bundle-Ether196': 99.5,
        'rointernetgye4:HundredGigE0/2/0/2': 75.5,
        'rointernetgye4:Bundle-Ether300': 96.1,
        'rointernetgye4:Bundle-Ether252': 49,
        'roclientesdcgye1:Bundle-Ether99': 56.6,
        'rointernetgye4:Bundle-Ether93': 14,
        'rointernetuio1:Bundle-Ether98': 14.4,
        'rointernetgye4:Bundle-Ether96': 96.3,
        'rointernetuio1:TenGigE0/3/0/1': 0.45,
        'rointernetuio1:Bundle-Ether106.50': 0,
    }
    match_results(gates, result)
    gates, gye, uio = reorder_gates(gates)
    display_gates(gates)
    saturada = gye[1]
    reference = get_reference_bw(saturada.capacidad)

    # === Testing
    best_gate = find_best_gate(saturada, gates, reference)
    locality = "UIO" if "uio" in saturada.gate else "GYE"
    attributes = analyze_attributes(best_gate, reference, locality, gates)
    logger.info(best_gate)
    for att in attributes:
        if att['score'] == 5:
            logger.info(att)
        elif att['score'] == 1 or att['score'] == 0:
            logger.error(att)
        else:
            logger.warning(att)
    assert best_gate is not None

