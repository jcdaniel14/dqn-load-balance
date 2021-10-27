from .q_learn_agent import QNAgent
from .q_learn_environment import QNEnv

import logging
import json

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("q-learn")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_usable_bw(capacidad):
    if capacidad >= 100:
        return round(capacidad * 0.949, 2)  # 0.001 de margen para evitar que identifique 190/190 como sin exceso cuando si esta saturada
    else:
        return round(capacidad * 0.899, 2)  # 0.001 de margen para evitar que identifique 190/190 como sin exceso cuando si esta saturada


def get_reference_bw(capacidad):
    if 0 <= capacidad <= 10:
        return 2
    elif 10 < capacidad <= 50:
        return 6
    elif 50 < capacidad:
        return 12


def is_not_solvable(links):
    excesos = 0
    for link in links:
        valid_bw = get_usable_bw(link['capacidad'])
        exceso = link['bw'] - valid_bw
        if exceso >= 0:
            excesos += exceso
            needed_bw = get_reference_bw(link['capacidad'])
            logger.info(f"Exceso de {exceso}, se debe mover {needed_bw}")
            if not has_bw_somewhere(needed_bw, links):
                return False, True

    return excesos == 0, False


def has_bw_somewhere(needed_bw, links):
    for link in links:
        valid_bw = get_usable_bw(link['capacidad'])
        available = valid_bw - link['bw']
        if available >= needed_bw:
            logger.info(f"Hay {available} disponibles en un enlace, suficientes para mover {needed_bw}")
            return True
    return False


def solve_congestion(links, path, debug=False, segments=100, epoch=5000) -> (list, list, list, list, str):
    # === Validacion inicial
    not_saturated, not_solvable = is_not_solvable(links)

    if not_saturated:
        return None, None, None, None, "Ninguna interfaz está saturada"
    elif not_solvable:
        return None, None, None, None, "No hay suficiente capacidad para descongestionar las salidas"
    else:
        logger.info("El problema es resolvible")
        # === Discount farsighted, futuras recompensas tienen el mismo peso que las actuales, epsilon random en un inicio, greedy despues
        save_links(links, path)
        env = QNEnv(links=links)
        agent = QNAgent(env=env, epsilon=1.0, eps_min=0.001, eps_decay=0.5, lr=0.03, discount=1.0)
        return agent.learn(path, debug=debug, segments=segments, epoch=epoch)


def save_links(links, path):
    with open(f"{path}/files/model.pt", 'w+') as f:
        f.write(json.dumps(links.tolist()))
