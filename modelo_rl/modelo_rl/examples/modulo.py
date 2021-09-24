import numpy as np
import modelo_rl
import os

path = os.path.dirname(os.path.abspath(__file__))

ejemplo2 = np.array([{'id': 'uio1-port1', 'bw': 191, 'congestionado': True, 'region': 'uio', 'capacidad': 200},
                     {'id': 'uio1-port2', 'bw': 96, 'congestionado': True, 'region': 'uio', 'capacidad': 100},
                     {'id': 'uio1-port3', 'bw': 50, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                     {'id': 'uio1-port4', 'bw': 50, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                     {'id': 'uio1-port5', 'bw': 50, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                     {'id': 'uio1-port6', 'bw': 55, 'congestionado': True, 'region': 'uio', 'capacidad': 60},
                     {'id': 'uio2-port1', 'bw': 200, 'congestionado': True, 'region': 'uio', 'capacidad': 200},
                     {'id': 'uio2-port2', 'bw': 200, 'congestionado': True, 'region': 'uio', 'capacidad': 200},
                     {'id': 'gye1-port1', 'bw': 100, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                     {'id': 'gye1-port2', 'bw': 25, 'congestionado': False, 'region': 'gye', 'capacidad': 50},
                     {'id': 'gye1-port3', 'bw': 50, 'congestionado': False, 'region': 'gye', 'capacidad': 100},
                     {'id': 'gye1-port4', 'bw': 100, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                     {'id': 'gye2-port1', 'bw': 100, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                     {'id': 'gye3-port1', 'bw': 50, 'congestionado': False, 'region': 'gye', 'capacidad': 100}
                     ])
acciones = modelo_rl.solve_congestion(ejemplo2, path, log_it=False, epoch=5000)
print(acciones)
