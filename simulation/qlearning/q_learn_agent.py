from qlearning.plotter import plot_mavg_sr

import pickle
import numpy as np
import logging
import os

logger = logging.getLogger('q-learn')
path = os.path.dirname(os.path.abspath(__file__))
WINDOW = 50


class QNAgent(object):
    """
    - Define el estado como la cantidad de enlaces saturados al momento de la medicion
    - Define la accion como un enlace escogido para resolver la saturacion
    - Define la recompensa en base a las politicas que optimizan la toma de decisiones
    - Define el estado terminal cuando ya no existen enlaces saturados
    """

    def __init__(self, env, epsilon=1.0, lr=0.1, discount=1.0, Q=None):
        # === Environment
        self.env = env
        self.Q = self.q_table() if Q is None else Q

        # === Hyper-parametros
        self.epsilon = epsilon
        self.lr = lr
        self.discount = discount

    def q_table(self):
        Q = {}
        for state in self.env.state_space:
            for action in self.env.possible_actions:
                Q[state, action] = 0  # Initial value of 0 encourages the model to try new options since any first move will return -1, -2 or -10 reward
        return Q

    def choose_action(self, state, epsilon=0, log=False):
        """
        - En base a la funcion Q, estima usando los valores de recompensa obtenidos anteriormente una decision que maximice la recompensa
        """
        idx = self.env.get_congested_link_idx()
        if np.random.random() > epsilon:
            values = np.array([self.Q[state, a] for a in self.env.possible_actions])
            action = np.argmax(values)
            if log:
                print(f"Enlace {idx + 1} saturado, se ha seleccionado el enlace {self.env.possible_actions[action] + 1}")
            return self.env.possible_actions[action]
        else:
            rand = np.random.choice(self.env.possible_actions)
            if log:
                print(f"Enlace {idx + 1} saturado, se ha seleccionado el enlace aleatorio {rand + 1}")
            return rand

    def decrement_epsilon(self, epoch, eps_min=0.01):
        decrement = 1 / (epoch / 2)
        self.epsilon = (self.epsilon - decrement) if self.epsilon > eps_min else eps_min

    # def decrement_epsilon(self, epoch):
    #     if self.epsilon - 2 / epoch > 0:
    #         logger.debug(f"Epsilon reduced to value: {self.epsilon}")
    #         self.epsilon -= 2 / epoch
    #     else:
    #         logger.debug(f"Epsilon = {self.epsilon}")
    #         self.epsilon = 0

    def learn(self, epoch=50):
        scores, eps_history, steps = [], [], []
        for i in range(1, epoch + 1):
            log_it = i % 10 == 0
            if log_it:
                print('================================starting epoch ', i)

            # === Siempre hace un reset al inicial un epoch
            done = False
            score = 0
            observation = self.env.reset()
            while not done:
                if log_it:
                    self.env.render("Start")
                # === Escoge una opcion en base a epsilon, aleatoria inicialmente y en base a la funcion Q a futuro
                action = self.choose_action(observation, self.epsilon, log=log_it)

                # === Realiza un step en el environment
                observation_, reward, done, info = self.env.step(action)

                # === Actualiza el acumulado de recompensas hasta llegar al estado terminal
                score += reward

                # === Calcula la mejor accion posible en base al estado actual
                action_ = self.choose_action(observation_, self.epsilon)

                # === Actualiza la funcion Q(s,a)
                self.Q[observation, action] = self.Q[observation, action] + self.lr * (
                        reward + self.discount * self.Q[observation_, action_] - self.Q[observation, action])
                # === Setea el nuevo estado como el estado actual de esta epoch
                observation = observation_
                if log_it:
                    self.env.render("End")

            # Guarda la recompensa de cada epoch para ser evaluada luego
            # if i % 10 == 0:
            scores.append(score)
            steps.append(i)
            eps_history.append(self.epsilon)

            # === Ejemplo de evolucion de epsilon en base a epochs -> 1 -> 0.8 -> 0.6 -> 0.4 -> 0.2 -> 0
            self.decrement_epsilon(epoch)

        # === Grafica el proceso de aprendizaje
        print(f"Final score: {scores[-1]} / Best Score: {max(scores)} / Perfect Score: -2")
        plot_mavg_sr(scores, eps_history, steps, f'Evolucion del entrenamiento (mavg={WINDOW})', 'Scores', 'Training Steps', window=WINDOW, filename=f"{path}/files/learning_curve.png")
        # === Guarda los valores de Q en un archivo
        self.save()

    def save(self):
        with open(f'{path}/files/q_table.pickle', 'wb') as f:
            pickle.dump(self.Q, f, pickle.HIGHEST_PROTOCOL)
