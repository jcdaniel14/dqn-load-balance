from .utils import print_link, save_links
import numpy as np
import logging

logger = logging.getLogger('q-learn')


def is_congested(bw, capacidad) -> bool:
    """
    - Retorna si el enlace esta congestionado:
    - Si es igual o mayor al 95% de capacidad para enlaces 100G/200G
    - Si es igual o mayor al 90% de capacidad para enlaces 10G/20G/50G/60G
    """
    if capacidad >= 100:
        return round(bw / capacidad, 2) >= 0.95
    else:
        return round(bw / capacidad, 2) >= 0.9


def get_training_links(path):
    links = np.array([{'id': 'uio1-port1', 'bw': 126, 'congestionado': False, 'region': 'uio', 'capacidad': 200},
                      {'id': 'uio1-port2', 'bw': 29, 'congestionado': False, 'region': 'uio', 'capacidad': 100},
                      {'id': 'uio1-port3', 'bw': 49, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                      {'id': 'uio1-port4', 'bw': 27, 'congestionado': False, 'region': 'uio', 'capacidad': 50},
                      {'id': 'uio1-port5', 'bw': 49, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                      {'id': 'uio1-port6', 'bw': 29, 'congestionado': False, 'region': 'uio', 'capacidad': 60},
                      {'id': 'uio2-port1', 'bw': 119, 'congestionado': False, 'region': 'uio', 'capacidad': 200},
                      {'id': 'uio2-port2', 'bw': 129, 'congestionado': False, 'region': 'uio', 'capacidad': 200},
                      {'id': 'gye1-port1', 'bw': 129, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                      {'id': 'gye1-port2', 'bw': 42, 'congestionado': False, 'region': 'gye', 'capacidad': 50},
                      {'id': 'gye1-port3', 'bw': 29, 'congestionado': False, 'region': 'gye', 'capacidad': 100},
                      {'id': 'gye1-port4', 'bw': 199, 'congestionado': True, 'region': 'gye', 'capacidad': 200},
                      {'id': 'gye2-port1', 'bw': 19, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                      {'id': 'gye3-port1', 'bw': 19, 'congestionado': False, 'region': 'gye', 'capacidad': 100}
                      ])
    save_links(links, path)
    return links


def calculate_reward(is_local, is_terminal_state):
    """
    - Define las recompensas en base al estado y la decision tomada
    -    0 Si es estado terminal y la decision fue un movimiento local
    -   -1 Si no es estado terminal y la decision fue un movimiento local
    -   -3 Si es estado terminal y la decision no fue un movimiento local
    -   -4 Si no es estado terminal y la decision no fue un movimiento local
    """
    reward = 0
    if not is_terminal_state:
        reward -= 1
    if not is_local:
        reward -= 3
    return reward


def get_reference_bw(capacidad):
    if 0 <= capacidad <= 10:
        return 2
    elif 10 < capacidad <= 50:
        return 6
    elif 50 < capacidad:
        return 12


class QNEnv(object):

    def __init__(self, links=None, path=None):
        # === Entorno
        self.links = get_training_links(path) if links is None else links
        # === Estado inicial (Observation) => # de interfaces saturadas
        self.initial_state = self.get_current_state()
        self.current_state = self.initial_state

        # === Espacio de estados / Todos los posibles estados incluyendo el estado terminal
        self.state_space = self.get_state_space()
        # === Posibles acciones => Indice de cada enlace
        self.possible_actions = np.arange(start=0, stop=len(self.links))

        # === Informativo
        self.congested_idx = 0
        self.chosen_idx = 0
        self.path = path

    def step(self, chosen_action):
        """
        - Recibe la accion a tomar por el modelo, sea aleatoria u optimizada mediante la funcion Q
        - Penaliza inmediatamente con -10 si la accion tomada es imposible, como mover tráfico hacia un enlace saturado
        - Setea el nuevo estado en base a la accion escogida
        - Retorna un estandar de pytorch (current_state, reward, is_terminal_state, debug_info)
        """

        # === Rueditas de seguridad por si el primer paso es un estado terminal
        if self.is_terminal_state():
            return self.current_state, 0, True, f"Environment is in terminal state already!. {self.links}"

        # === Informativo
        self.chosen_idx = chosen_action
        self.congested_idx = self.get_congested_link_idx()

        # === Siempre habra minimo un enlace saturado o el proceso habria entrado en estado terminal
        chosen_link = self.links[self.chosen_idx]
        congested_link = self.links[self.congested_idx]
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
        self.links = get_training_links(self.path) if links is None else links
        self.initial_state = self.get_current_state()
        self.current_state = self.initial_state
        return self.initial_state

    def render(self, title):
        print(f'-------------{title}-------------')
        for idx, link in enumerate(self.links):
            print_link(link, idx == self.congested_idx, idx == self.chosen_idx, title)
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
        """
        - Retorna los posibles estados de saturacion desde 0 hasta n enlaces saturados
        """
        return np.arange(0, len(self.links) + 1).tolist()

    def get_current_state(self):
        """
        - Retorna la cantidad de enlaces saturados
        """
        state = 0
        for link in self.links:
            if link['congestionado']:
                state += 1
        return state
