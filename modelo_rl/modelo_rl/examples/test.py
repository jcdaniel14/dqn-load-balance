ls = {}
item = (1, 2)
item2 = (2, 3)
t = (item,item2)
print(t)

# import numpy as np
# links = np.array(
#         [
#             {'congestionado': True, 'bw': 196, 'local': 'gye', 'capacidad': 200},
#             {'congestionado': False, 'bw': 56, 'local': 'gye', 'capacidad': 100},
#             {'congestionado': True, 'bw': 197, 'local': 'uio', 'capacidad': 200},
#             {'congestionado': False, 'bw': 39, 'local': 'uio', 'capacidad': 50},
#         ])
#
# state = []
# for link in links:
#     sat = 1 if link['congestionado'] else 0
#     local = 1 if link['local'] == "uio" else 0
#     state.append((sat, local))
#
# print(state)

#
def decimalToBinary(n, length):
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


def get_state_space(links, features):
    states = []
    states_len = 2 ** (len(links) * features)
    for i in range(states_len):
        states.append(to_tuple(decimalToBinary(i, len(links) * features), features))
    return states


states = get_state_space(links=[1, 2, 3, 4], features=2)
for state in states:
    print(state)
print(len(states))
