import numpy as np
import modelo_rl
import os
from log import init_logger

path = os.path.dirname(os.path.abspath(__file__))
logger = init_logger('testing', file=False)
i = 0
last_scores = []
for i in range(1):
    ejemplo2 = np.array([{'id': 'uio1-port1', 'bw': 192, 'congestionado': True, 'region': 'uio', 'capacidad': 200},  # 0
                         {'id': 'uio1-port2', 'bw': 95, 'congestionado': True, 'region': 'uio', 'capacidad': 100},  # 1
                         {'id': 'uio1-port3', 'bw': 46, 'congestionado': True, 'region': 'uio', 'capacidad': 50},  # 2
                         {'id': 'uio1-port4', 'bw': 46, 'congestionado': True, 'region': 'uio', 'capacidad': 50},  # 3
                         {'id': 'uio1-port5', 'bw': 46, 'congestionado': True, 'region': 'uio', 'capacidad': 50},  # 4
                         {'id': 'uio1-port6', 'bw': 56, 'congestionado': True, 'region': 'uio', 'capacidad': 60},  # 5
                         {'id': 'uio2-port1', 'bw': 184, 'congestionado': False, 'region': 'uio', 'capacidad': 200},  # 6
                         {'id': 'uio2-port2', 'bw': 189, 'congestionado': False, 'region': 'uio', 'capacidad': 200},  # 7
                         {'id': 'gye1-port1', 'bw': 184, 'congestionado': False, 'region': 'gye', 'capacidad': 200},  # 8
                         {'id': 'gye1-port2', 'bw': 43, 'congestionado': False, 'region': 'gye', 'capacidad': 50},  # 9
                         {'id': 'gye1-port3', 'bw': 92, 'congestionado': False, 'region': 'gye', 'capacidad': 100},  # 10
                         {'id': 'gye1-port4', 'bw': 188, 'congestionado': False, 'region': 'gye', 'capacidad': 200},  # 11
                         {'id': 'gye2-port1', 'bw': 184, 'congestionado': False, 'region': 'gye', 'capacidad': 200},  # 12
                         {'id': 'gye3-port1', 'bw': 93, 'congestionado': False, 'region': 'gye', 'capacidad': 100}  # 13
                         ])
    acciones, scores, _, _, err = modelo_rl.solve_congestion(ejemplo2, path, debug=True, epoch=5000)
    if err:
        logger.info(err)
    elif scores:
        last_scores.append(scores[-1])
        i += 1
        logger.info(f"Round {i}")
print(last_scores)
