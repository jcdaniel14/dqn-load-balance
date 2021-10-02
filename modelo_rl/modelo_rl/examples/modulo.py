import numpy as np
import modelo_rl
import os
from log import init_logger

path = os.path.dirname(os.path.abspath(__file__))
logger = init_logger('testing', file=False)
i = 0
last_scores = []
for i in range(100):
    ejemplo2 = np.array([{'id': 'uio1-port1', 'bw': 126, 'congestionado': False, 'region': 'uio', 'capacidad': 200},
                         {'id': 'uio1-port2', 'bw': 29, 'congestionado': False, 'region': 'uio', 'capacidad': 100},
                         {'id': 'uio1-port3', 'bw': 49, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                         {'id': 'uio1-port4', 'bw': 27, 'congestionado': False, 'region': 'uio', 'capacidad': 50},
                         {'id': 'uio1-port5', 'bw': 49, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                         {'id': 'uio1-port6', 'bw': 29, 'congestionado': False, 'region': 'uio', 'capacidad': 60},
                         {'id': 'uio2-port1', 'bw': 119, 'congestionado': False, 'region': 'uio', 'capacidad': 200},
                         {'id': 'uio2-port2', 'bw': 129, 'congestionado': False, 'region': 'uio', 'capacidad': 200},
                         {'id': 'gye1-port1', 'bw': 129, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                         {'id': 'gye1-port2', 'bw': 42, 'congestionado': False, 'region': 'gye', 'capacidad': 50},
                         {'id': 'gye1-port3', 'bw': 29, 'congestionado': False, 'region': 'gye', 'capacidad': 100},
                         {'id': 'gye1-port4', 'bw': 199, 'congestionado': True, 'region': 'gye', 'capacidad': 200},
                         {'id': 'gye2-port1', 'bw': 19, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                         {'id': 'gye3-port1', 'bw': 19, 'congestionado': False, 'region': 'gye', 'capacidad': 100}
                         ])
    acciones, scores, _, _, _ = modelo_rl.solve_congestion(ejemplo2, path, debug=False, epoch=5000)
    last_scores.append(scores[-1])
    i += 1
    logger.info(f"Round {i}")
print(last_scores)
