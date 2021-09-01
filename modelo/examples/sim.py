class bcolors:
    WHITE = '\033[1m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    SAT = '\033[90;43m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def printline(line, color):
    print(f"{color}{line}{bcolors.ENDC}")


def print_link(link):
    if link['capacidad'] >= 100:
        saturado = round(link['bw'] - (0.95 * link['capacidad']), 2)
    else:
        saturado = round(link['bw'] - (0.9 * link['capacidad']), 2)

    baseline = link['capacidad'] / 100

    cap = int(link['capacidad'] // baseline)
    bw = int(link['bw'] // baseline)
    sat = int(saturado // baseline)
    sat = 0 if sat < 0 else sat

    # print(cap)
    # print(bw)
    # print(sat)

    fill = "█"
    fill2 = "░"
    len1 = (bw - sat) * fill
    len2 = sat * fill
    len3 = (cap - bw) * fill2

    print(f"{bcolors.SAT}Link 1:{bcolors.ENDC} {color1}{len1}{bcolors.ENDC}{color2}{len2}{bcolors.ENDC}{bcolors.WHITE}{len3}{bcolors.ENDC}")


color1 = bcolors.OKBLUE
color2 = bcolors.WARNING
link1 = {'capacidad': 100, 'bw': 96}
link2 = {'capacidad': 200, 'bw': 196}
link22 = {'capacidad': 200, 'bw': 177}
link3 = {'capacidad': 50, 'bw': 45}

print_link(link1)
print_link(link2)
print_link(link22)
print_link(link3)
