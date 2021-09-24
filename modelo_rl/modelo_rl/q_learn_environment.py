from .utils import print_link
import numpy as np
import logging

logger = logging.getLogger('q-learn')


def is_congested(bw, capacidad) -> bool:
    if capacidad >= 100:
        return round(bw / capacidad, 2) >= 0.95
    else:
        return round(bw / capacidad, 2) >= 0.9


def get_training_links():
    return np.array(
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
    elif 10 < capacidad <= 50:
        return 6
    elif 50 < capacidad:
        return 12


class QNEnv(object):

    def __init__(self, links=None):
        # === Entorno y estado inicial (Observation)
        self.links = get_training_links() if links is None else links
        self.initial_state = self.get_current_state()
        self.current_state = self.initial_state

        # === Espacio de estados / Todos los posibles estados excluyendo el estado terminal
        self.state_space = self.get_state_space()
        # === Posibles acciones
        self.possible_actions = np.arange(start=0, stop=len(self.links))

        # === Informativo
        self.congested_idx = 0
        self.chosen_idx = 0

    def step(self, chosen_action):
        """
        - Recibe la accion a tomar por el modelo, sea aleatoria u optimizada mediante la funcion Q
        - Penaliza inmediatamente con -10 si la accion tomada es imposible, como mover tráfico hacia un enlace saturado
        - Setea el nuevo estado en base a la accion escogida
        - Retorna un estandar de pytorch (current_state, reward, is_terminal_state, debug_info)
        """
        # === Informativo
        self.chosen_idx = chosen_action
        self.congested_idx = self.get_congested_link_idx()

        chosen_link = self.links[self.chosen_idx]
        congested_link = self.links[self.congested_idx]  # Siempre habra minimo un enlace saturado o el proceso habria entrado en estado terminal
        reference_bw = get_reference_bw(congested_link['capacidad'])

        # === Si el enlace seleccionado está congestionado
        if self.links[chosen_action]['congestionado']:
            return self.current_state, -10, False, f"Link chosen {chosen_action} is currently saturated"
        # === Si el enlace seleccionado estará congestionado después del movimiento
        elif is_congested(chosen_link['bw'] + reference_bw, chosen_link['capacidad']):
            return self.current_state, -10, False, f"Link chosen {chosen_action} will be saturated"
        # === Si el enlace seleccionado es el mismo enlace saturado
        elif self.chosen_idx == self.congested_idx:
            return self.current_state, -10, False, f"Link chosen {chosen_action} is the same saturated link, WTF"
        else:
            reward, is_terminal_state = self.set_state(congested_link, chosen_link)
            return self.current_state, reward, is_terminal_state, None

    def set_state(self, congested_link, chosen_link):
        """
        - Simula el movimiento de trafico hacia el enlace escogido por el modelo
        - Calcula el nuevo estado o # de links congestionados
        - Retorna la recompensa en base a las politicas establecidas y la accion realizada
        """
        # === Valor de tráfico de referencia que se va a mover
        reference_bw = get_reference_bw(congested_link['capacidad'])

        congested_link['bw'] -= reference_bw
        congested_link['congestionado'] = is_congested(congested_link['bw'], congested_link['capacidad'])
        chosen_link['bw'] += reference_bw
        chosen_link['congestionado'] = is_congested(chosen_link['bw'], chosen_link['capacidad'])

        # === Setea el estado actual
        self.current_state = self.get_current_state()

        # === Parametros para determinar la recompensa
        is_local = congested_link['region'] == chosen_link['region']
        is_terminal_state = self.is_terminal_state()
        return calculate_reward(is_local, is_terminal_state), is_terminal_state

    def reset(self, links=None) -> list:
        """
        - Al finalizar un epoch, se resetea el entorno para calcular las recompensas de un nuevo proceso de aprendizaje
        """
        self.links = get_training_links() if links is None else links
        self.initial_state = self.get_current_state()
        return self.initial_state

    def render(self, title):
        print(f'-------------{title}-------------')
        for idx, link in enumerate(self.links):
            print_link(link, idx, idx == self.congested_idx, idx == self.chosen_idx, title)
        if title == "End":
            print('--------------------------')

    def is_terminal_state(self) -> bool:
        """
        - Basicamente es estado terminal o fin del juego cuando el numero de links congestionados es 0
        """
        return self.current_state == 0

    def get_congested_link_idx(self) -> int:
        """
        - Prioriza los enlaces saturados con mayor capacidad
        """
        congested = list(filter(lambda x: x['congestionado'], self.links))
        if len(congested) > 0:
            congested = sorted(congested, key=lambda x: x['capacidad'], reverse=True)
            return np.where(self.links == congested[0])[0][0]
        else:
            return None

    def get_state_space(self):
        states = []
        for i in range(len(self.links)):
            states.append(i)
        return states

    def get_current_state(self):
        state = 0
        for link in self.links:
            if link['congestionado']:
                state += 1
        return state

    # === BW Actual fuera del environment
    # def get_current_state(self):
    #     state = []
    #     for link in self.links:
    #         sat = 1 if link['congestionado'] else 0
    #         local = 1 if link['region'] == "uio" else 0
    #         state.append((sat, local))
    #     return tuple(state)

    # def get_state_space(self, features=2):
    #     states = []
    #     states_len = 2 ** (len(self.links) * features)
    #     logger.warning(f"Longitud de state space {states_len}")
    #     for i in range(states_len):
    #         states.append(to_tuple(decimal_to_bin(i, len(self.links) * features), features))
    #     logger.info("State space completado")
    #     return states
