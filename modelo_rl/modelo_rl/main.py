from .q_learn_agent import QNAgent
from .q_learn_environment import QNEnv

import logging

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("q-learn")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


def solve_congestion(links, path):
    # === Discount farsighted, futuras recompensas tienen el mismo peso que las actuales, epsilon random en un inicio, greedy despues
    env = QNEnv(links=links)
    agent = QNAgent(env=env, epsilon=1.0, eps_min=0.001, lr=0.1, discount=1.0)
    return agent.learn(path, epoch=1000)
