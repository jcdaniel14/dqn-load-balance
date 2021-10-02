import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import json


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    SAT = '\033[90;43m'
    FREE = '\033[90;42m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def save_links(links, path):
    with open(f"{path}/files/model.pt", 'w+') as f:
        f.write(json.dumps(links.tolist()))


def decimal_to_bin(n, length):
    tmp = bin(n).replace("0b", "")
    if len(tmp) < length:
        for i in range(length - len(tmp)):
            tmp = "0" + tmp
        return tmp
    else:
        return tmp


def to_tuple(line, features):
    tmp = []
    for i in range(0, len(line), features):
        tmp.append((int(line[i]), int(line[i + 1])))
    return tuple(tmp)


def plot_learning(x, scores, epsilons, lines=None, filename='learning_curve.png'):
    sns.set(style="whitegrid", font="Lato")
    fig = plt.figure(figsize=(22, 8))
    ax = fig.add_subplot(111, label="1")
    ax2 = fig.add_subplot(111, label="2", frame_on=False)

    ax.plot(x, epsilons, color="#008013")
    ax.set_xlabel("Training Steps", color="#008013")
    ax.set_ylabel("Epsilon", color="#008013")
    ax.tick_params(axis='x', colors="#008013")
    ax.tick_params(axis='y', colors="#008013")

    N = len(scores)
    running_avg = np.empty(N)
    for t in range(N):
        running_avg[t] = np.mean(scores[max(0, t - 20):(t + 1)])

    ax2.scatter(x, running_avg, color="#069AF3")
    ax2.axes.get_xaxis().set_visible(False)
    ax2.yaxis.tick_right()
    ax2.set_ylabel('Score', color="#069AF3")
    ax2.yaxis.set_label_position('right')
    ax2.tick_params(axis='y', colors="#069AF3")

    if lines is not None:
        for line in lines:
            plt.axvline(x=line)
    print(x)
    print(scores)
    print(epsilons)
    plt.plot()
    plt.show()
    plt.savefig(filename)


def print_link(link, congested, chosen, title):
    color1 = bcolors.OKBLUE
    color2 = bcolors.WARNING

    if link['capacidad'] >= 100:
        saturado = round(link['bw'] - (0.95 * link['capacidad']), 2)
    else:
        saturado = round(link['bw'] - (0.9 * link['capacidad']), 2)

    baseline = link['capacidad'] / 100

    cap = int(link['capacidad'] // baseline)
    bw = int(link['bw'] // baseline)
    sat = int(saturado // baseline)
    sat = 0 if sat < 0 else sat

    fill = "█"
    fill2 = "░"
    len1 = (bw - sat) * fill
    len2 = sat * fill
    len3 = (cap - bw) * fill2

    if title == "End":
        if congested:
            print(
                f"{bcolors.SAT}Link {link['id']}:{bcolors.ENDC} {color1}{len1}{bcolors.ENDC}{color2}{len2}{bcolors.ENDC}{len3} ({link['bw']}/{link['capacidad']})Gbps")
        elif chosen:
            print(
                f"{bcolors.FREE}Link {link['id']}:{bcolors.ENDC} {color1}{len1}{bcolors.ENDC}{color2}{len2}{bcolors.ENDC}{len3} ({link['bw']}/{link['capacidad']})Gbps")
        else:
            print(
                f"Link {link['id']}: {color1}{len1}{bcolors.ENDC}{color2}{len2}{bcolors.ENDC}{bcolors.BOLD}{len3}{bcolors.ENDC} ({link['bw']}/{link['capacidad']})Gbps")
    else:
        print(
            f"Link {link['id']}: {color1}{len1}{bcolors.ENDC}{color2}{len2}{bcolors.ENDC}{bcolors.BOLD}{len3}{bcolors.ENDC} ({link['bw']}/{link['capacidad']})Gbps")
