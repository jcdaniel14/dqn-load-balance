import numpy as np
import modelo_rl
import os
path = os.path.dirname(os.path.abspath(__file__))

ejemplo = np.array(
        [
            {'id': 'gye1-port1', 'congestionado': True, 'bw': 199, 'region': 'gye', 'capacidad': 200},
            {'id': 'gye1-port2', 'congestionado': False, 'bw': 187, 'region': 'gye', 'capacidad': 200},
            {'id': 'gye1-port3', 'congestionado': False, 'bw': 156, 'region': 'gye', 'capacidad': 200},
            {'id': 'gye2-port1', 'congestionado': False, 'bw': 49, 'region': 'gye', 'capacidad': 100},
            {'id': 'gye2-port2', 'congestionado': True, 'bw': 48, 'region': 'gye', 'capacidad': 50},
            {'id': 'uio1-port1', 'congestionado': False, 'bw': 120, 'region': 'uio', 'capacidad': 200},
            {'id': 'uio1-port2', 'congestionado': True, 'bw': 199, 'region': 'uio', 'capacidad': 200},
            {'id': 'uio2-port1', 'congestionado': False, 'bw': 100, 'region': 'uio', 'capacidad': 200},
            {'id': 'uio2-port2', 'congestionado': False, 'bw': 50, 'region': 'uio', 'capacidad': 100},
            {'id': 'uio2-port3', 'congestionado': False, 'bw': 29, 'region': 'uio', 'capacidad': 60},
        ])
path = f"{path}/learning_curve.png"
acciones = modelo_rl.solve_congestion(ejemplo, path)
print(acciones)
