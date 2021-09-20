from plotter import plot_mavg_sr
import os

WINDOW = 1
path = os.path.dirname(os.path.abspath(__file__))

x = ["2020-01", "2020-02", "2020-03", "2020-04", "2020-05", "2020-06", "2020-07", "2020-08", "2020-09", "2020-10"]
y = [40, 30, 25, 55, 120, 90, 43, 77, 59, 97]
y2 = [3.5, 4, 3.2, 4.2, 3.1, 3.9, 4.7, 3.3, 5.1, 4.3]
plot_mavg_sr(y, y2, x, f'Tiempo de resolución (1 enlace saturado)', 'Duración (min)', '@timestamp', window=WINDOW, filename=f"{path}/files/learning_curve.png")
