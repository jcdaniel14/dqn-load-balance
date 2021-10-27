import numpy as np
import modelo_rl
import os
from log import init_logger

path = os.path.dirname(os.path.abspath(__file__))
logger = init_logger('testing', file=False)
i = 0
last_scores = []
for i in range(1):
    ejemplo2 = np.array([{'id': 'uio1-port1', 'bw': 193, 'congestionado': True, 'region': 'uio', 'capacidad': 200},
                         {'id': 'uio1-port2', 'bw': 96, 'congestionado': True, 'region': 'uio', 'capacidad': 100},
                         {'id': 'uio1-port3', 'bw': 45, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                         {'id': 'uio1-port4', 'bw': 47, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                         {'id': 'uio1-port5', 'bw': 48, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                         {'id': 'uio1-port6', 'bw': 57, 'congestionado': True, 'region': 'uio', 'capacidad': 60},
                         {'id': 'uio2-port1', 'bw': 193, 'congestionado': True, 'region': 'uio', 'capacidad': 200},
                         {'id': 'uio2-port2', 'bw': 198, 'congestionado': True, 'region': 'uio', 'capacidad': 200},
                         {'id': 'gye1-port1', 'bw': 103, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                         {'id': 'gye1-port2', 'bw': 33, 'congestionado': False, 'region': 'gye', 'capacidad': 50},
                         {'id': 'gye1-port3', 'bw': 88, 'congestionado': False, 'region': 'gye', 'capacidad': 100},
                         {'id': 'gye1-port4', 'bw': 127, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                         {'id': 'gye2-port1', 'bw': 119, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                         {'id': 'gye3-port1', 'bw': 59, 'congestionado': False, 'region': 'gye', 'capacidad': 100}])
    acciones, scores, epoch, steps, err = modelo_rl.solve_congestion(ejemplo2, path, debug=True, segments=5000, epoch=15000)
    print(acciones)
    if err:
        logger.info(err)
    elif scores:
        last_scores.append(scores[-1])
        i += 1
        logger.info(f"Round {i}")
print(last_scores)
