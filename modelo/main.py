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


def example_links():
    return np.array(
        [
            {'congestionado': False, 'bw': 50, 'local': 'uio', 'capacidad': 100},
            {'congestionado': True, 'bw': 9, 'local': 'gye', 'capacidad': 10},
            {'congestionado': True, 'bw': 10, 'local': 'gye', 'capacidad': 10},
            {'congestionado': False, 'bw': 2, 'local': 'uio', 'capacidad': 10}
        ])


def load_agent():
    Q = load_table()
    env = QNEnv(example_links())
    agent = QNAgent(Q=Q, env=env)
    initial_state = agent.env.reset()
    action = agent.choose_action(initial_state)


def load_table():
    with open(f'{path}/files/q_table.pickle', 'rb') as f:
        return pickle.load(f)


def learn():
    # === Discount farsighted, futuras recompensas tienen el mismo peso que las actuales, epsilon random en un inicio, greedy despues
    env = QNEnv()
    agent = QNAgent(env=env, epsilon=1.0, lr=0.1, discount=1.0)
    agent.learn()


if __name__ == '__main__':
    if LEARN:
        learn()
    else:
        load_agent()
