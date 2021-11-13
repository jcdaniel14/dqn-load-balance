from modelo_rl import QNAgent, QNEnv
from plotly import graph_objs as go, io as pio
import colorlover as cl
import pandas as pd
import json
import numpy as np
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


def get_usable_bw(capacidad):
    if capacidad >= 100:
        return round(capacidad * 0.949, 2)  # 0.001 de margen para evitar que identifique 190/190 como sin exceso cuando si esta saturada
    else:
        return round(capacidad * 0.899, 2)  # 0.001 de margen para evitar que identifique 190/190 como sin exceso cuando si esta saturada


def get_reference_bw(capacidad):
    if 0 <= capacidad <= 10:
        return 2
    elif 10 < capacidad <= 50:
        return 6
    elif 50 < capacidad:
        return 12


def is_not_solvable(links):
    excesos = 0
    for link in links:
        valid_bw = get_usable_bw(link['capacidad'])
        exceso = link['bw'] - valid_bw
        if exceso >= 0:
            excesos += exceso
            needed_bw = get_reference_bw(link['capacidad'])
            logger.info(f"Exceso de {exceso}, se debe mover {needed_bw}")
            if not has_bw_somewhere(needed_bw, links):
                return False, True

    return excesos == 0, False


def has_bw_somewhere(needed_bw, links):
    for link in links:
        valid_bw = get_usable_bw(link['capacidad'])
        available = valid_bw - link['bw']
        if available >= needed_bw:
            logger.info(f"Hay {available} disponibles en un enlace, suficientes para mover {needed_bw}")
            link["bw"] += needed_bw
            return True
    return False


def get_palette(size):
    """Get the suitable palette of a certain size"""
    if size <= 8:
        palette = cl.scales[str(max(3, size))]['qual']['Set2']
    else:
        palette = cl.interp(cl.scales['8']['qual']['Set2'], size)
    return palette


def create_layout(title, y_title, x_title, x_type=None, width=800, height=600, layout_kwargs=None):
    """simplified method to generate Layout"""
    layout = go.Layout(
        title={"text": title, "font": {"family": "Quicksand"}},
        legend=dict(x=0.0, y=-0.15, orientation='h'),
        yaxis=dict(rangemode='tozero', title=y_title),
        xaxis=dict(type=x_type, title=x_title),
        width=width, height=height,
        margin=go.layout.Margin(l=30, r=30, t=30, b=30),
        showlegend=True,
    )
    layout.update(layout_kwargs)
    return layout


def srs_mavg(sr_list, window):
    df = pd.DataFrame(sr_list)
    sma = df.rolling(window=window, min_periods=1).mean()
    rstd = df.rolling(window=window, min_periods=1).std()

    upperband = sma + rstd
    lowerband = sma - rstd
    return sma[0], upperband[0], lowerband[0]


def lower_opacity(rgb, opacity):
    return rgb.replace('rgb(', 'rgba(').replace('hsl(', 'hsla(').replace(')', f', {opacity})')


def plot_multi(plots, title, y_title, x_title, window=20, filename="eps_greedy.png"):
    data = []
    colors = ["#FFB55F", "#14607A", "#E76B74"]
    # colors = get_palette(len(plots))
    i = 0
    for lr, obj in plots.items():
        color = colors[i]
        i += 1
        sma, upper_band, lower_band = srs_mavg(obj['y'], window)
        graph = go.Scatter(
            x=obj['x'], y=sma, showlegend=True,
            line={'color': color, 'width': 1.5},
            fillcolor=lower_opacity(color, 0.15),
            name=lr
        )
        upper = go.Scatter(
            x=obj['x'], y=upper_band, showlegend=False,
            line={'color': color, 'width': 0},
            fillcolor=lower_opacity(color, 0.15),
        )
        lower = go.Scatter(
            x=obj['x'], y=lower_band, showlegend=False,
            line={'color': color, 'width': 0},
            fill='tonexty', fillcolor=lower_opacity(color, 0.15),
        )
        data.append(graph)
        # data.append(upper)
        # data.append(lower)

    layout = create_layout(title=title, y_title=y_title, x_title=x_title)
    fig = go.Figure(data, layout)
    fig.update_layout(font_family="Quicksand")
    fig.show()
    save_image(fig, filename)
    return


def save_image(figure, filepath):
    try:
        pio.write_image(figure, filepath, scale=2)
    except Exception as e:
        print(e)


def grid_search():
    # === Discount farsighted, futuras recompensas tienen el mismo peso que las actuales, epsilon random en un inicio, greedy despues
    links = example_links()
    save_links(links, path)
    not_saturated, not_solvable = is_not_solvable(links)
    if not_saturated:
        return None, None, None, None, "Ninguna interfaz está saturada"
    elif not_solvable:
        logger.error("Not solvable")
        return None, None, None, None, "No hay suficiente capacidad para descongestionar las salidas"
    else:
        logger.info("Its solvable")

    env = QNEnv(links=example_links(), path=path)
    # discounts = [0, 1]
    # lrs = [0.01, 0.1, 1]
    eps = [0, 0.5]
    plots = {}
    # escenario de epsilon greedy
    for e in eps:
        # for d in discounts:
        agent = QNAgent(env=env, epsilon=1.0, eps_decay=e, eps_min=0.01, lr=0.1, discount=1.0)
        ba, scores, _, steps, _ = agent.learn(epoch=5000, debug=True, segments=5000, path=path)
        print(f"Best actions: {ba}")
        print(f"Max Score: {max(scores)}")
        # name = f"\u03B1={lr}|\u03B4={d}"
        name = "\u03B5=0"
        if e == 0.5:
            name = "\u03B5=1 (decreciente)"
        elif e == 1:
            name = "\u03B5=1 (constante)"

        final_score = []
        for score in scores:
            tmp = score if score >= -800 else -800
            final_score.append(tmp)
        plots[name] = {'y': final_score, 'x': steps}

    plot_multi(plots, "Grid Search - Epsilon", "Scores", "Training Steps", window=20)


def example_links():
    return np.array([{'id': 'uio1-port1', 'bw': 196, 'congestionado': True, 'region': 'uio', 'capacidad': 200},
                     {'id': 'uio1-port2', 'bw': 85, 'congestionado': True, 'region': 'uio', 'capacidad': 100},
                     {'id': 'uio1-port3', 'bw': 49, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                     {'id': 'uio1-port4', 'bw': 27, 'congestionado': False, 'region': 'uio', 'capacidad': 50},
                     {'id': 'uio1-port5', 'bw': 49, 'congestionado': True, 'region': 'uio', 'capacidad': 50},
                     {'id': 'uio1-port6', 'bw': 39, 'congestionado': False, 'region': 'uio', 'capacidad': 60},
                     {'id': 'uio2-port1', 'bw': 196, 'congestionado': True, 'region': 'uio', 'capacidad': 200},
                     {'id': 'uio2-port2', 'bw': 196, 'congestionado': True, 'region': 'uio', 'capacidad': 200},
                     {'id': 'gye1-port1', 'bw': 129, 'congestionado': False, 'region': 'gye', 'capacidad': 200},
                     {'id': 'gye1-port2', 'bw': 49, 'congestionado': True, 'region': 'gye', 'capacidad': 50},
                     {'id': 'gye1-port3', 'bw': 89, 'congestionado': False, 'region': 'gye', 'capacidad': 100},
                     {'id': 'gye1-port4', 'bw': 199, 'congestionado': True, 'region': 'gye', 'capacidad': 200},
                     {'id': 'gye2-port1', 'bw': 199, 'congestionado': True, 'region': 'gye', 'capacidad': 200},
                     {'id': 'gye3-port1', 'bw': 88, 'congestionado': False, 'region': 'gye', 'capacidad': 100}
                     ])


def save_links(links, path):
    with open(f"{path}/files/model.pt", 'w+') as f:
        f.write(json.dumps(links.tolist()))


if __name__ == '__main__':
    grid_search()
