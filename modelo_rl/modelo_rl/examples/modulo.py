import numpy as np
import modelo_rl
import os

path = os.path.dirname(os.path.abspath(__file__))

ejemplo2 = np.array([{'id': 'uio1-port1', 'bw': 185, 'congestionado': False, 'region': 'uio', 'capacidad': 200},
                     {'id': 'uio1-port2', 'bw': 92, 'congestionado': False, 'region': 'uio', 'capacidad': 100},
                     {'id': 'uio1-port3', 'bw': 43, 'congestionado': False, 'region': 'uio', 'capacidad': 50},
                     {'id': 'uio1-port4', 'bw': 43, 'congestionado': False, 'region': 'uio', 'capacidad': 50},
                     {'id': 'uio1-port5', 'bw': 33, 'congestionado': False, 'region': 'uio', 'capacidad': 50},
                     {'id': 'uio1-port6', 'bw': 51, 'congestionado': False, 'region': 'uio', 'capacidad': 60},
                     {'id': 'uio2-port1', 'bw': 101, 'congestionado': False, 'region': 'uio', 'capacidad': 200},
                     {'id': 'uio2-port2', 'bw': 101, 'congestionado': False, 'region': 'uio', 'capacidad': 200},
                     {'id': 'gye1-port1', 'bw': 194, 'congestionado': True, 'region': 'gye', 'capacidad': 200},
                     {'id': 'gye1-port2', 'bw': 26, 'congestionado': False, 'region': 'gye', 'capacidad': 50},
                     {'id': 'gye1-port3', 'bw': 51, 'congestionado': False, 'region': 'gye', 'capacidad': 100},
                     {'id': 'gye1-port4', 'bw': 101, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                     {'id': 'gye2-port1', 'bw': 101, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                     {'id': 'gye3-port1', 'bw': 51, 'congestionado': False, 'region': 'gye', 'capacidad': 100}]
                    )
acciones = modelo_rl.solve_congestion(ejemplo2, path, epoch=1000)
print(acciones)
