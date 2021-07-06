import logging
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger('tesis')


class Network(object):
    def __init__(self):
        self.links = np.array(
            [{'is_saturated': True, 'bw': 10, 'local': 'gye'}, {'is_saturated': True, 'bw': 9, 'local': 'quito'}, {'is_saturated': False, 'bw': 2}])
        self.stateSpace = [1, 2, 3, 4]  # 1 2 3
        self.stateSpacePlus = [0, 1, 2, 3, 4]
        self.actionSpace = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
        self.possibleActions = ['A', 'B', 'C']
        self.congestedLinks = 2

    def isTerminalState(self, state):  # State is links state in general
        logger.info("Calculating terminal state")
        return state in self.stateSpacePlus and state not in self.stateSpace

    def setState(self, network_state, link_chosen):
        """
        - Moves traffic from first saturated link to chosen link
        - Calculates state -> number of saturated links
        """
        logger.info("Setting state")
        for link in network_state:
            if link['is_saturated']:
                link['bw'] -= 2
                network_state[link_chosen]['bw'] += 2
                network_state[link_chosen]['is_saturated'] = network_state[link_chosen]['bw'] >= 9
                link['is_saturated'] = network_state[link_chosen]['bw'] >= 9
                break

        count = 0
        for link in network_state:
            if link['is_saturated']:
                count += 1
        self.congestedLinks = count  # state actual
        return

    def step(self, action):
        """
        - Gets the actual state
            - Links with bandwidth and saturation state
        - Executes the action
            - Chooses a link, and moves the traffic from first (most important?) saturated gate to this link
        - Calculates the reward
            - -1 for each movement that does not resolve terminal state, -10 for saturating another link, 0 if its terminal state
        - If its legal move updates the state and returns GYM compliant
            - Only illegal move is to move towards own link
        """
        logger.info(f"Stepping into action {action}")
        link_chosen = self.actionSpace[action]  # A, B, C
        if self.links[link_chosen]['is_saturated']:
            return self.congestedLinks, -10, self.isTerminalState(self.congestedLinks), f"Link chosen {link_chosen} is currently saturated"
        else:
            self.setState(self.links, link_chosen)
            reward = -1 if not self.isTerminalState(self.congestedLinks) else 0
            return self.congestedLinks, reward, self.isTerminalState(self.congestedLinks), None

    def reset(self):
        """
        - At the end of every episode (epoch?) we have to reset the environment for a new learning to occurr
        """
        logger.info("Resetting board")
        self.links = np.array([{'is_saturated': True, 'bw': 10}, {'is_saturated': True, 'bw': 9}, {'is_saturated': False, 'bw': 2}])
        self.congestedLinks = 2  # state
        return self.congestedLinks

    def render(self):
        print('--------------------------')
        for idx, link in enumerate(self.links):
            print(f"{idx + 1} -> BW:{link['bw']} (Saturated:{link['is_saturated']})")
        print('--------------------------')

    def actionSpaceSample(self):
        logger.info("Choosing random action")
        return np.random.choice(self.possibleActions)


def maxAction(Q, state, actions):
    """
    - Calculate array of agent's estimate of expected future rewards for the state that's in, and all possible actions
    - Return action that gives the most value
    """
    logger.info("Maximaxing future reward before choosing my action")
    values = np.array([Q[state, a] for a in actions])
    action = np.argmax(values)
    return actions[action]


if __name__ == '__main__':
    env = Network()

    lr = 0.1
    discount = 1.0  # Farsighted, count future rewards equally
    epsilon = 1.0  # Random strategy at first, purely greedy strategy later

    Q = {}
    for state in env.stateSpacePlus:
        for action in env.possibleActions:
            Q[state, action] = 0  # Setting the initial return to 0 encourages the model to try new options since any first move will return -1 reward

    numGames = 10
    totalRewards = np.zeros(numGames)
    env.render()

    for i in range(numGames):
        # if i % 50 == 0:
        print('starting game ', i)

        # === Always done at the start of a new game
        done = False  # Terminal state
        epRewards = 0
        observation = env.reset()

        while not done:
            logger.info("Initial network state")
            env.render()
            # === Choose action, random at first, maximizing rewards later
            rand = np.random.random()
            action = maxAction(Q, observation, env.possibleActions) if rand < (1 - epsilon) else env.actionSpaceSample()

            # === Take step into the environment
            observation_, reward, done, info = env.step(action)

            # === Keep track of this game's rewards
            epRewards += reward

            # === Calculate best next action, based on actual state
            action_ = maxAction(Q, observation_, env.possibleActions)

            # === Update the Q Function
            Q[observation, action] = Q[observation, action] + lr * (reward + discount * Q[observation_, action_] - Q[observation, action])
            # === Set new state as the state
            observation = observation_
            logger.info("Final network state")
            env.render()

        # Setting epsilon to pure greedy
        if epsilon - 2 / numGames > 0:
            epsilon -= 2 / numGames
        else:
            epsilon = 0

        totalRewards[i] = epRewards

    plt.plot(totalRewards)
    plt.show()
