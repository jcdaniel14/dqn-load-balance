from q_learn_agent import QNAgent
from q_learn_environment import QNEnv

import numpy as np
import pickle
import logging
import os

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("q-learn")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

LEARN = True
path = os.path.dirname(os.path.abspath(__file__))


def load_agent():
    Q = load_table()
    # for k, v in Q.items():
    #     if v != 0:
    #         print(k)
    env = QNEnv(links=example_links())
    agent = QNAgent(Q=Q, env=env)
    initial_state = agent.env.reset(links=example_links())
    action = agent.choose_action(initial_state, log=True)


def load_table():
    with open(f'{path}/files/q_table.pickle', 'rb') as f:
        return pickle.load(f)


def learn():
    # === Discount farsighted, futuras recompensas tienen el mismo peso que las actuales, epsilon random en un inicio, greedy despues
    env = QNEnv()
    agent = QNAgent(env=env, epsilon=1.0, lr=0.1, discount=1.0)
    agent.learn(epoch=1000)


def example_links():
    return np.array(
        [
            {'congestionado': True, 'bw': 199, 'local': 'gye', 'capacidad': 200},
            {'congestionado': True, 'bw': 197, 'local': 'gye', 'capacidad': 200},
            {'congestionado': True, 'bw': 196, 'local': 'gye', 'capacidad': 200},
            {'congestionado': True, 'bw': 99, 'local': 'gye', 'capacidad': 100},
            {'congestionado': True, 'bw': 48, 'local': 'gye', 'capacidad': 50},
            {'congestionado': False, 'bw': 120, 'local': 'uio', 'capacidad': 200},
            {'congestionado': False, 'bw': 129, 'local': 'uio', 'capacidad': 200},
            {'congestionado': False, 'bw': 100, 'local': 'uio', 'capacidad': 200},
            {'congestionado': False, 'bw': 50, 'local': 'uio', 'capacidad': 100},
            {'congestionado': False, 'bw': 29, 'local': 'uio', 'capacidad': 60},
        ])


if __name__ == '__main__':
    if LEARN:
        learn()
    else:
        load_agent()
