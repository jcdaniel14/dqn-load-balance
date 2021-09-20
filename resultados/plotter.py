from plotly import graph_objs as go, io as pio
from plotly.subplots import make_subplots
import colorlover as cl
import pandas as pd


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
        title=title,
        legend={"orientation": "h"},
        yaxis=dict(rangemode='tozero', title=y_title),
        xaxis=dict(type=x_type, title=x_title),
        width=width, height=height,
        margin=go.layout.Margin(l=60, r=30, t=60, b=60),
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


def plot_mavg_sr(y, y2, x, title, y_title, x_title, window=20, filename="learning_curve.png"):
    sma, upper_band, lower_band = srs_mavg(y, window)
    color = "rgb(20,96,122)"
    color2 = "rgb(255,181,95)"
    main_trace = go.Scatter(
        x=x, y=sma, mode='lines', showlegend=True,
        line={'color': color, 'width': 1.5}, name="Manual"
    )
    epsilon = go.Scatter(
        x=x, y=y2, mode='lines', showlegend=True,
        line={'color': color2, 'width': 1.5}, name="RL"
    )
    data = [main_trace, epsilon]
    layout = create_layout(title=title, y_title=y_title, x_title=x_title)
    fig = go.Figure(data, layout)
    fig.show()
    save_image(fig, filename)
    return


def save_image(figure, filepath):
    try:
        pio.write_image(figure, filepath, scale=2)
    except Exception as e:
        print(e)
