from modelo_rl import QNAgent, QNEnv
from plotly import graph_objs as go, io as pio
import colorlover as cl
import pandas as pd

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


def get_palette(size):
    """Get the suitable palette of a certain size"""
    if size <= 8:
        palette = cl.scales[str(max(3, size))]['qual']['Set2']
    else:
        palette = cl.interp(cl.scales['8']['qual']['Set2'], size)
    return palette


def create_layout(title, y_title, x_title, x_type=None, width=800, height=500, layout_kwargs=None):
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


def plot_multi(plots, title, y_title, x_title, window=20, filename="learning_rate.png"):
    data = []
    colors = ["#FFB55F", "#14607A", "#E76B74"]
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
    env = QNEnv(path=path)
    eps = [0, 0.25, 1]
    lrs = [0.001, 0.01, 0.1, 1]
    plots = {}
    # for lr in lrs:
    for e in eps:
        agent = QNAgent(env=env, epsilon=1.0, eps_decay=e, eps_min=0.001, lr=0.1, discount=1.0)
        _, scores, _, steps, _ = agent.learn(epoch=10000, path=path)
        name = "e=1 (constante)"
        if e == 0.25:
            name = "e=1 (decreciente)"
        elif e == 0:
            name = "e=0"
        plots[name] = {'y': scores, 'x': steps}

    plot_multi(plots, "Grid Search - Epsilon", "Scores", "Training Steps", window=50)


def example_links():
    return np.array(
        [
            {'congestionado': True, 'bw': 199, 'region': 'gye', 'capacidad': 200},
            {'congestionado': True, 'bw': 197, 'region': 'gye', 'capacidad': 200},
            {'congestionado': True, 'bw': 196, 'region': 'gye', 'capacidad': 200},
            {'congestionado': True, 'bw': 99, 'region': 'gye', 'capacidad': 100},
            {'congestionado': True, 'bw': 48, 'region': 'gye', 'capacidad': 50},
            {'congestionado': False, 'bw': 120, 'region': 'uio', 'capacidad': 200},
            {'congestionado': False, 'bw': 129, 'region': 'uio', 'capacidad': 200},
            {'congestionado': False, 'bw': 100, 'region': 'uio', 'capacidad': 200},
            {'congestionado': False, 'bw': 50, 'region': 'uio', 'capacidad': 100},
            {'congestionado': False, 'bw': 29, 'region': 'uio', 'capacidad': 60},
        ])


if __name__ == '__main__':
    grid_search()
