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


def get_excess(links):
    excesos, disponibles = 0, 0
    for link in links:
        valid_bw = get_usable_bw(link['capacidad'])
        exceso = link['bw'] - valid_bw
        exceso = exceso if exceso >= 0 else 0

        disponible = valid_bw - link['bw']
        disponible = disponible if disponible >= 0 else 0
        logger.warning(f"Enlace {link['id']} - Exceso: {exceso:.2f} - Disponible: {disponible:.2f}")

        excesos += exceso
        disponibles += disponible

    return excesos, disponibles


def solve_congestion(links, path, debug=False, segments=100, epoch=1000) -> (list, list, list, list, str):
    # === Validacion inicial
    exceso, capacidad_disponible = get_excess(links)

    if exceso == 0:
        return None, None, None, None, "Ninguna interfaz está saturada"
    elif exceso >= capacidad_disponible:
        return None, None, None, None, "No hay suficiente capacidad para descongestionar las salidas"
    else:
        # === Discount farsighted, futuras recompensas tienen el mismo peso que las actuales, epsilon random en un inicio, greedy despues
        save_links(links, path)
        env = QNEnv(links=links)
        agent = QNAgent(env=env, epsilon=1.0, eps_min=0.001, lr=0.1, discount=1.0)
        return agent.learn(path, debug=debug, segments=segments, epoch=epoch)


def save_links(links, path):
    with open(f"{path}/files/model.pt", 'w+') as f:
        f.write(json.dumps(links.tolist()))
