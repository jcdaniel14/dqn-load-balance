from utils import expired_info
from dataframes import get_df_subnets, get_df_gate
from tsmoothie.smoother import LowessSmoother
from dateutil import tz

import tele
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import json
import logging
import subprocess
import sys
import os

# === CONSTANTS
logger = logging.getLogger("health-monitor")
logger.setLevel(logging.INFO)


def generate_chart_rollback(subred, destino, bucket_value):
    logger.info("Generando chart y enviando notificacion a Telegram.")
    # === Suavizado
    smoother = LowessSmoother(smooth_fraction=0.03, iterations=1)
    subnet_values = get_df_subnets([subred], destino)
    subnet_df = pd.DataFrame(subnet_values, columns=['date', 'value'])

    gate_values = get_df_gate(destino)
    df = pd.DataFrame(gate_values)
    df.date = pd.to_datetime(df["date"], unit='s')
    df.value = df.value / 1000_000_000
    smoother.smooth(df["value"])
    df['gate'] = smoother.smooth_data[0]

    subnet_df.value = subnet_df.value / 1000_000_000

    max_len = len(df.index) if len(df.index) <= len(subnet_df.index) else len(subnet_df.index)
    df = df.iloc[:max_len]
    subnet_df = subnet_df.iloc[:max_len]

    smoother.smooth(subnet_df["value"])
    df['subnet'] = smoother.smooth_data[0]

    generate_chart(df, destino.gate, subred['net'])
    tele.send(f"El prefijo {subred['net']} [{bucket_value}G] puede retornar a su salida original {destino.gate} [{destino.current_gbps}G]")
    tele.send_image(f"Tráfico actual de salida original y prefijo ({subred['net']})", destino.gate)
    # tele.send("Por favor, utilizar la aplicacion para confirmar el retorno de la red.")
    return


def generate_chart_and_send(origen, mejores_subredes, destino, bucket_value):
    logger.info("Generando chart y enviando notificacion a Telegram.")
    # === Suavizado
    smoother = LowessSmoother(smooth_fraction=0.03, iterations=1)
    subnet_values = get_df_subnets(mejores_subredes, origen)
    subnet_df = pd.DataFrame(subnet_values, columns=['date', 'value'])

    gate_values = get_df_gate(origen)
    df = pd.DataFrame(gate_values)
    df.date = pd.to_datetime(df["date"], unit='s')
    df.value = df.value / 1000_000_000
    smoother.smooth(df["value"])
    df['gate'] = smoother.smooth_data[0]

    subnet_df.value = subnet_df.value / 1000_000_000

    max_len = len(df.index) if len(df.index) <= len(subnet_df.index) else len(subnet_df.index)
    df = df.iloc[:max_len]
    subnet_df = subnet_df.iloc[:max_len]

    smoother.smooth(subnet_df["value"])
    df['subnet'] = smoother.smooth_data[0]

    inline = ""
    for s in mejores_subredes:
        inline += f"{s['net']} - "
    inline = inline[:-2]
    generate_chart(df, origen.gate, inline)
    tele.send(f"La salida {origen.gate} [{origen.current_gbps}G] se encuentra saturada, se sugiere mover {round(bucket_value,2)}G hacia {destino.gate} [{destino.current_gbps}G]")
    tele.send_image(f"Tráfico actual de salida saturada y redes a mover ({inline})", origen.gate)
    # tele.send("Por favor, utilizar la aplicacion para confirmar el movimiento de redes.")
    return


def generate_chart(df, gate, subnet):
    sns.set(style="whitegrid", font="Lato")
    # === Define plot dimensions (22x8 inches)
    dims = (22, 8)
    fig, ax = plt.subplots(figsize=dims)

    # === Stackplot
    ax.fill_between(df.date, df.gate, color="#34F5C5", edgecolor="#21D0B2", linewidth=2, alpha=0.5)
    ax.fill_between(df.date, df.subnet, color="#1DCDFE", linewidth=1, alpha=0.5)
    sns.lineplot(df.date, df.subnet, color="#1DCDFE", ax=ax, linestyle="-")
    ax.lines[0].set_linestyle("--")

    # === X-axis date formatting to Month-Year on Jan, Month every other tick
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d %H:%M", tz=tz.gettz("America/Guayaquil")))

    # === Define Y-label & no X-label
    ax.set_xlabel("")
    ax.set_ylabel(f"Tráfico (Gbps)", fontsize=14)
    # === Define legend at bottom with no frame & font-size
    plt.legend(["Subnet Traffic", "Port Traffic"], loc="lower center", bbox_to_anchor=(0.5, -0.3), frameon=False,
               fontsize=14, ncol=2)
    fig.subplots_adjust(bottom=0.25)
    # === Define bottom Title & superior Title
    ax.set_title("Ultimas 24 horas", y=-0.2, loc="left", fontsize=27, fontweight=700)
    plt.suptitle(f"{gate} - {subnet}", ha="left", x=0.125, y=0.93, fontsize=21)

    # === Save to file with dpi=200
    if os.name == 'nt':
        path = f"C:/Users/gsantiago/PycharmProjects/2021/logs/health-monitor/{gate.replace(':', '_').replace('/','_')}.png"
    else:
        path = f"/var/log/python/health-monitor/uploads/{gate.replace(':', '_').replace('/','_')}.png"
    fig.savefig(path, dpi=200)
    # plt.show()


def get_network_bw(gate, network):
    # return 0.4  # TODO produccion
    cmd = f"/home/gsantiago/go_2020/netflow/network_bw/network_bw --gate {gate} --subnet {network}"
    output = subprocess.run([cmd], stdout=subprocess.PIPE, shell=True).stdout.decode("utf-8")
    if output.find("{") == -1:
        send_error("No se logro detectar el BW (Network BW). Favor revisar en Go")
    output = output[output.find("{"):].strip().strip("\n")
    rs = json.loads(output)
    net = rs['response']['network']
    if not expired_info(net):
        return round(net['bps'] / 1000_000_000, 2)
    else:
        logger.error("Consulta Netflow devuelve un timestamp expirado, por favor revisar el Netflow.")
        return -1


def find_current_bw_netflow():
    logger.info("Obteniendo BW actual de las salidas seleccionadas via Netflow.")
    # result = {"rointernetuio1:Bundle-Ether90": 8.54,
    #           "roclientesdcgye1:Bundle-Ether99": 9.5,
    #           "rointernetgye4:Bundle-Ether96": 95.6,
    #           "rointernetgye4:TenGigE0/0/0/5": 5.71,
    #           "rointernetuio1:TenGigE0/3/0/1": 0.42,
    #           "roclientesdcgye2:TenGigE0/0/0/12": 4.47,
    #           "roclientesdcgye1:TenGigE0/0/0/18": 6.25,
    #           "roclientesdcgye1:Bundle-Ether98": 25.02,
    #           "rointernetuio1:HundredGigE0/0/0/2": 59.28,
    #           "rointernetuio1:Bundle-Ether98": 5.02,
    #           "rointernetgye4:HundredGigE0/2/0/2": 47.11,
    #           "rointernetgye4:Bundle-Ether252": 27.81,
    #           "roclientesdcgye2:Bundle-Ether95": 12.9,
    #           "rointernetuio1:Bundle-Ether106.50": 7.51,
    #           "rointernetuio1:Bundle-Ether93": 11.27,
    #           "rointernetuio1:Bundle-Ether95": 14.21,
    #           "routercdn2uio:HundredGigE0/0/0/1": 19.27,
    #           "rointernetgye4:Bundle-Ether93": 15.88,
    #           "rointernetgye4:Bundle-Ether250": 14.62,
    #           "rointernetuio1:Bundle-Ether105.100": 73.65}
    # return result # TODO produccion
    result = dict()
    cmd = "/home/gsantiago/go_2020/netflow/internet_status/internet_status"
    output = subprocess.run([cmd], stdout=subprocess.PIPE, shell=True).stdout.decode("utf-8")
    if output.find("{") == -1:
        send_error("No se logro detectar el BW (Internet Status). Favor revisar en Go")
    output = output[output.find("{"):].strip().strip("\n")
    rs = json.loads(output)

    for item in rs["response"]:
        gate = f"{item['exporter']}:{item['name']}"
        result[gate] = item['currentTraffic']
    return result


def find_top_subnets(gate):
    logger.info("Obteniendo el top 20 de redes de la salida saturada via Netflow.")
    # result = [
    #     # {'net': '181.199.32.0/19', 'bps': 6067289244.444446, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '181.199.62.0/24', 'bps': 3468907155.555556, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '181.199.59.0/24', 'bps': 2241782799.9999995, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '181.199.58.0/23', 'bps': 2241782799.9999995, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '181.199.54.0/24', 'bps': 210186488.88888887, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '200.110.64.0/19', 'bps': 99458177.77777778, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '181.199.56.0/24', 'bps': 83915422.22222222, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '181.199.56.0/23', 'bps': 83915422.22222222, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '181.199.55.0/24', 'bps': 62497377.77777778, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '64.46.64.0/19', 'bps': 33430711.11111111, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '8.242.218.0/24', 'bps': 755955.5555555555, 'ts': '2021-02-03 09:36:00'},
    #     {'net': '69.65.128.0/19', 'bps': 369022.22222222225, 'ts': '2021-02-03 09:36:00'}]
    # return result # TODO produccion
    result = []
    cmd = f"/home/gsantiago/go_2020/netflow/top_lite/top_subnets --exporter {gate.router} --port {gate.name} --top 20 -o {gate.os_type}"
    logger.info(f"CMD: {cmd}")
    output = subprocess.run([cmd], stdout=subprocess.PIPE, shell=True).stdout.decode("utf-8")
    if output.find("{") == -1:
        send_error(f"No se logro detectar el top de subredes para {gate} (Top Subnets). Favor revisar en Go")
    output = output[output.find("{"):].strip().strip("\n")
    rs = json.loads(output)

    for item in rs["response"]["subnets"]:
        result.append(item)
    return result


def send_error(msg):
    rs = {"status": "error", "error": msg}
    print(json.dumps(rs))
    sys.exit(0)
