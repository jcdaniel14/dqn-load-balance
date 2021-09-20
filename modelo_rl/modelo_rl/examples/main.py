import numpy as np
import matplotlib.pyplot as plt


class GridWorld(object):
    def __init__(self, m, n, magicSquares):
        self.grid = np.zeros((m, n))
        self.m = m
        self.n = n
        self.stateSpace = [i for i in range(self.m * self.n)]
        self.stateSpace.remove(self.m * self.n - 1)
        self.stateSpacePlus = [i for i in range(self.m * self.n)]
        self.actionSpace = {'U': -self.m, 'D': self.m, 'L': -1, 'R': 1}
        self.possibleActions = ['U', 'D', 'L', 'R']
        self.addMagicSquares(magicSquares)
        self.agentPosition = 0

    def addMagicSquares(self, magicSquares):
        self.magicSquares = magicSquares
        i = 2
        for square in magicSquares:
            x = square // self.m
            y = square % self.n
            self.grid[x][y] = i
            i += 1
            x = magicSquares[square] // self.m
            y = magicSquares[square] % self.n
            self.grid[x][y] = i
            i += 1

    def isTerminalState(self, state):
        return state in self.stateSpacePlus and state not in self.stateSpace

    def getAgentRowAndColumn(self):
        x = self.agentPosition // self.m
        y = self.agentPosition % self.n
        return x, y

    def setState(self, state):
        """
        - Assumes it is a legal move
        - State is a number from 0 to MxN
        - In the grid, 0 is represented as empty square, 1 as the agent
        """
        x, y = self.getAgentRowAndColumn()
        self.grid[x][y] = 0
        self.agentPosition = state
        x, y = self.getAgentRowAndColumn()
        self.grid[x][y] = 1

    def offGridMove(self, newState, oldState):
        """
        - Taking the modulus against m as zero represents we're on the edge,
        """
        if newState not in self.stateSpacePlus:
            return True
        elif oldState % self.m == 0 and newState % self.m == self.m - 1:
            return True
        elif oldState % self.m == self.m - 1 and newState % self.m == 0:
            return True
        else:
            return False

    def step(self, action):
        """
        - Gets the actual state
        - Executes the given action and updates the position
        - Calculates the reward
        - If its a legal move updates the state and returns GYM compliant (newState, reward, isTerminal, debugInfo)
        """
        x, y = self.getAgentRowAndColumn()
        resultingState = self.agentPosition + self.actionSpace[action]
        if resultingState in self.magicSquares.keys():
            resultingState = self.magicSquares[resultingState]

        reward = -1 if not self.isTerminalState(resultingState) else 0
        if not self.offGridMove(resultingState, self.agentPosition):
            self.setState(resultingState)
            return resultingState, reward, self.isTerminalState(self.agentPosition), None
        else:
            return self.agentPosition, reward, self.isTerminalState(self.agentPosition), None

    def reset(self):
        """
        - At the end of every episode (epoch?) we have to reset the environment for a new learning to occurr
        """
        self.agentPosition = 0
        self.grid = np.zeros((self.m, self.n))
        self.addMagicSquares(self.magicSquares)
        return self.agentPosition

    def render(self):
        print('--------------------------')
        for row in self.grid:
            for col in row:
                if col == 0:
                    print('-', end='\t')
                elif col == 1:
                    print('X', end='\t')
                elif col == 2:
                    print('Ain', end='\t')
                elif col == 3:
                    print('Aout', end='\t')
                elif col == 4:
                    print('Bin', end='\t')
                elif col == 5:
                    print('Bout', end='\t')
            print('\n')
        print('--------------------------')

    def actionSpaceSample(self):
        return np.random.choice(self.possibleActions)


def maxAction(Q, state, actions):
    """
    - Calculate array of agent's estimate of expected future rewards for the state that's in, and all possible actions
    - Return action that gives the most value
    """
    values = np.array([Q[state, a] for a in actions])
    action = np.argmax(values)
    return actions[action]


if __name__ == '__main__':
    magicSquares = {18: 54, 63: 14}
    env = GridWorld(9, 9, magicSquares)

    lr = 0.1
    discount = 1.0  # Farsighted, count future rewards equally
    epsilon = 1.0  # Random strategy at first, purely greedy strategy later

    Q = {}
    for state in env.stateSpacePlus:
        for action in env.possibleActions:
            Q[state, action] = 0  # Setting the initial return to 0 encourages the model to try new options since any first move will return -1 reward

    numGames = 27000
    totalRewards = np.zeros(numGames)
    env.render()

    for i in range(numGames):
        if i % 5000 == 0:
            print('starting game ', i)

        # === Always done at the start of a new game
        done = False  # Terminal state
        epRewards = 0
        observation = env.reset()

        while not done:
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

        # Setting epsilon to pure greedy
        if epsilon - 2 / numGames > 0:
            epsilon -= 2 / numGames
        else:
            epsilon = 0

        totalRewards[i] = epRewards

    plt.plot(totalRewards)
    plt.show()
