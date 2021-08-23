import numpy as np
import logging

logger = logging.getLogger('q-learn')


def is_congested(link) -> bool:
    if link['capacidad'] >= 100:
        return round(link['bw'] / link['capacidad'], 2) >= 0.95
    else:
        return round(link['bw'] / link['capacidad'], 2) >= 0.9


def get_training_links():
    return np.array(
        [
            {'congestionado': True, 'bw': 90, 'local': 'uio', 'capacidad': 100},
            {'congestionado': False, 'bw': 2, 'local': 'gye', 'capacidad': 10},
            {'congestionado': True, 'bw': 10, 'local': 'gye', 'capacidad': 10},
            {'congestionado': False, 'bw': 2, 'local': 'uio', 'capacidad': 50}
        ])


def calculate_reward(is_local, is_terminal_state):
    """
    - Define las recompensas en base al estado y la decision tomada
    -    0 Si es estado terminal y la decision fue un movimiento local
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


def get_reference_bw(capacidad):
    if 0 <= capacidad <= 10:
        return 2
    elif 10 < capacidad <= 60:
        return 6
    elif 60 < capacidad:
        return 10


class QNEnv(object):

    def __init__(self, links=None):
        # === Entorno y estado inicial (Observation)
        self.links = get_training_links() if links is None else links
        self.initial_state = self.calculate_congested()
        self.current_state = self.initial_state

        # === Espacio de estados / Todos los posibles estados excluyendo el estado terminal
        self.state_space = np.arange(start=1, stop=len(self.links) + 1)
        # === Espacio de estados / Todos los posibles estados incluyendo el estado terminal
        self.state_space_plus = np.arange(start=0, stop=len(self.links) + 1)
        # === Posibles acciones
        self.possible_actions = np.arange(start=0, stop=len(self.links))

    def step(self, chosen_action):
        """
        - Recibe la accion a tomar por el modelo, sea aleatoria u optimizada mediante la funcion Q
        - Penaliza inmediatamente con -10 si la accion tomada es imposible, como mover tráfico hacia un enlace saturado
        - Setea el nuevo estado en base a la accion escogida
        - Retorna un estandar de pytorch (current_state, reward, is_terminal_state, debug_info)
        """
        if self.links[chosen_action]['congestionado']:
            return self.current_state, -10, False, f"Link chosen {chosen_action} is currently saturated"
        else:
            reward, is_terminal_state = self.set_state(self.links, chosen_action)
            return self.current_state, reward, is_terminal_state, None

    def set_state(self, links, chosen_action):
        """
        - Simula el movimiento de trafico hacia el enlace escogido por el modelo
        - Calcula el nuevo estado o # de links congestionados
        - Retorna la recompensa en base a las politicas establecidas y la accion realizada
        """
        congested_link = links[self.get_congested_link_idx()]  # Siempre habra minimo un enlace saturado o el proceso habria entrado en estado terminal
        chosen_link = links[chosen_action]

        # === Valor de tráfico de referencia que se va a mover
        reference_bw = get_reference_bw(congested_link['capacidad'])

        congested_link['bw'] -= reference_bw
        congested_link['congestionado'] = is_congested(congested_link)
        chosen_link['bw'] += reference_bw
        chosen_link['congestionado'] = is_congested(chosen_link)

        # === Setea el estado actual
        self.current_state = self.calculate_congested()

        # === Parametros para determinar la recompensa
        is_local = congested_link['local'] == chosen_link['local']
        is_terminal_state = self.is_terminal_state(self.current_state)
        return calculate_reward(is_local, is_terminal_state), is_terminal_state

    def reset(self) -> list:
        """
        - Al finalizar un epoch, se resetea el entorno para calcular las recompensas de un nuevo proceso de aprendizaje
        """
        self.links = get_training_links()
        self.initial_state = self.calculate_congested()
        return self.initial_state

    def render(self, title):
        print(f'-------------{title}-------------')
        for idx, link in enumerate(self.links):
            print(f"Enlace {idx + 1} - Capacidad: {link['capacidad']} - BW:{link['bw']} - Region: {link['local']} - (Saturated:{link['congestionado']})")
        print('--------------------------')

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

    def calculate_congested(self) -> int:
        key = [x['congestionado'] for x in self.links]
        return sum(key)
