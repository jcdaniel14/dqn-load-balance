import logging
import numpy as np
import matplotlib.pyplot as plt

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("tesis")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


def calculate_congested(links) -> int:
    key = [x['congestionado'] for x in links]
    return sum(key)


def is_congested(link) -> bool:
    """
    TODO En la practica depende de la capacidad del enlace para determinar a que nivel esta congestionado, de momento congestionado si supera 90%
    """
    return round(link['bw'] / link['capacidad'], 2) >= 0.9


def calculate_reward(is_local, is_terminal_state):
    """
    - Define las recompensas en base al estado y la decision tomada
    -   0 Si es estado terminal y la decision fue un movimiento local
    -   -1 Si es estado terminal y la decision no fue un movimiento local
    -   -1 Si no es estado terminal y la decision fue un movimiento local
    -   -2 Si no es estado terminal y la decision no fue un movimiento local
    """
    reward = 0
    if not is_terminal_state:
        reward -= 1
    if not is_local:
        reward -= 1
    return reward


class Network(object):
    """
    - Define el estado como la cantidad de enlaces saturados al momento de la medicion
    - Define la accion como un enlace escogido para resolver la saturacion
    - Define la recompensa en base a las politicas que optimizan la toma de decisiones
    - Define el estado terminal cuando ya no existen enlaces saturados
    TODO Deberia haber un estado terminal si despues de varias iteraciones no logra resolver la saturacion?, Ejemplo: si todas las interfaces estan saturadas
    """

    def __init__(self, links):
        # === Variable inicial, usado para resetear el environment y state al realizar un nuevo epoch
        self.original_links = links
        # === Entorno
        self.links = links
        # === Espacio de estados / Todos los posibles estados excluyendo el estado terminal
        self.state_space = np.arange(start=1, stop=len(links) + 1)
        # === Espacio de estados / Todos los posibles estados incluyendo el estado terminal
        self.state_space_plus = np.arange(start=0, stop=len(links) + 1)
        # === Posibles acciones
        self.possible_actions = np.arange(start=0, stop=len(links))
        # === Estado inicial
        self.congested_links = calculate_congested(self.links)

    def reset(self, links) -> bool:
        """
        - Al finalizar un epoch, se resetea el entorno para calcular las recompensas de un nuevo proceso de aprendizaje
        """
        self.links = links
        self.congested_links = calculate_congested(self.links)
        return self.congested_links

    def is_terminal_state(self, state) -> bool:
        """
        - Basicamente es estado terminal o fin del juego cuando el numero de links congestionados es 0
        """
        return state in self.state_space_plus and state not in self.state_space

    def get_congested_link_idx(self) -> int:
        """
        - Prioriza los enlaces saturados con mayor capacidad
        """
        congested = list(filter(lambda x: x['congestionado'], self.links))
        congested = sorted(congested, key=lambda x: x['capacidad'], reverse=True)
        return np.where(self.links == congested[0])[0][0]

    def set_state(self, links, chosen_action):
        """
        - Simula el movimiento de trafico hacia el enlace escogido por el modelo
        - Calcula el nuevo estado o # de links congestionados
        - Retorna la recompensa en base a las politicas establecidas y la accion realizada
        """
        is_local = False
        congested_link = links[self.get_congested_link_idx()]  # Siempre habra minimo un enlace saturado o el proceso habria entrado en estado terminal
        chosen_link = links[chosen_action]

        # === Valor de tráfico de referencia que se va a mover
        # TODO Este valor en la practica es variable, depende de la capacidad del enlace, podria incluirse cuando el funcionamiento del modelo esté estable
        reference_bw = 2 if chosen_link['local'] == 'gye' else 3

        congested_link['bw'] -= reference_bw
        congested_link['congestionado'] = is_congested(congested_link)
        chosen_link['bw'] += reference_bw
        chosen_link['congestionado'] = is_congested(chosen_link)

        # === Parametros para determinar la recompensa
        is_local = congested_link['local'] == chosen_link['local']
        self.congested_links = calculate_congested(self.links)
        is_terminal_state = self.is_terminal_state(self.congested_links)
        return calculate_reward(is_local, is_terminal_state), is_terminal_state

    def step(self, chosen_action):
        """
        - Recibe la accion a tomar por el modelo, sea aleatoria u optimizada mediante la funcion Q
        - Penaliza inmediatamente con -10 si la accion tomada es imposible, como mover tráfico hacia un enlace saturado
        - Setea el nuevo estado en base a la accion escogida
        - Retorna un estandar de pytorch (current_state, reward, is_terminal_state, debug_info)
        """
        if self.links[chosen_action]['congestionado']:
            return self.congested_links, -10, False, f"Link chosen {chosen_action} is currently saturated"
        else:
            reward, is_terminal_state = self.set_state(self.links, chosen_action)
            return self.congested_links, reward, is_terminal_state, None

    def render(self, title):
        print(f'-------------{title}-------------')
        for idx, link in enumerate(self.links):
            print(f"Link {idx + 1} - Capacidad: {link['capacidad']} - BW:{link['bw']} - Region: {link['local']} - (Saturated:{link['congestionado']})")
        print('--------------------------')

    def actionSpaceSample(self):
        logger.debug("Choosing random action")
        return np.random.choice(self.possible_actions)


def maxAction(Q, state, actions):
    """
    - En base a la funcion Q, estima usando los valores de recompensa obtenidos anteriormente una decision que maximice la recompensa
    """
    values = np.array([Q[state, a] for a in actions])
    action = np.argmax(values)
    return actions[action]


if __name__ == '__main__':
    env = Network(np.array(
        [
            {'congestionado': True, 'bw': 90, 'local': 'uio', 'capacidad': 100},
            {'congestionado': False, 'bw': 2, 'local': 'gye', 'capacidad': 10},
            {'congestionado': True, 'bw': 10, 'local': 'gye', 'capacidad': 10},
            {'congestionado': False, 'bw': 2, 'local': 'uio', 'capacidad': 10}
        ]))

    lr = 0.1
    discount = 1.0  # Farsighted, count future rewards equally
    epsilon = 1.0  # Random strategy at first, purely greedy strategy later

    Q = {}
    for state in env.state_space_plus:
        for action in env.possible_actions:
            Q[
                state, action] = 0  # Setting the initial return to 0 encourages the model to try new options since any first move will return -1, -2 or -10 reward

    num_games = 50
    total_rewards = np.zeros(num_games)

    for i in range(num_games):
        # if i % 50 == 0:
        print('starting game ', i)

        # === Always reset done at the start of a new game
        done = False
        epoch_rewards = 0
        # TODO Python pasa todos los datos por referencia, por lo que para inicializar o resetear, toca quemar el codigo hasta buscar una mejor solucion
        observation = env.reset(np.array(
            [
                {'congestionado': True, 'bw': 90, 'local': 'uio', 'capacidad': 100},
                {'congestionado': False, 'bw': 2, 'local': 'gye', 'capacidad': 10},
                {'congestionado': True, 'bw': 10, 'local': 'gye', 'capacidad': 10},
                {'congestionado': False, 'bw': 2, 'local': 'uio', 'capacidad': 10}
            ]))

        while not done:
            env.render("Start")
            # === Escoge una opcion en base a epsilon, aleatoria inicialmente, en base a la funcion Q a futuro
            rand = np.random.random()
            action = maxAction(Q, observation, env.possible_actions) if rand < (1 - epsilon) else env.actionSpaceSample()

            # === Realiza un step en el environment
            observation_, reward, done, info = env.step(action)

            # === Actualiza el acumulado de recompensas hasta llegar al estado terminal
            epoch_rewards += reward

            # === Calcula la mejor accion posible en base al estado actual
            action_ = maxAction(Q, observation_, env.possible_actions)

            # === Actualiza la funcion Q
            Q[observation, action] = Q[observation, action] + lr * (reward + discount * Q[observation_, action_] - Q[observation, action])
            # === Setea el nuevo estado como el estado actual de esta epoch
            observation = observation_
            env.render("End")

        # Ejemplo de evolucion de epsilon con 10 num_games -> 1 -> 0.8 -> 0.6 -> 0.4 -> 0.2 -> 0
        if epsilon - 2 / num_games > 0:
            logger.debug(f"Epsilon reduced to greedy: {epsilon}")
            epsilon -= 2 / num_games
        else:
            logger.debug(f"Epsilon = {epsilon}")
            epsilon = 0

        # Guarda la recompensa de cada epoch para ser evaluada luego
        total_rewards[i] = epoch_rewards

    plt.plot(total_rewards)
    plt.show()
