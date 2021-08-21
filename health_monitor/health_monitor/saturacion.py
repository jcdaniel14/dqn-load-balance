from objects import Port
import logging

logger = logging.getLogger('health-monitor')


def find_best_gate(saturada, gates, reference) -> Port:
    logger.info(f"Determinando la mejor salida global para descongestionar a {saturada.gate}")
    gates = find_good_gate(gates, reference)

    if len(gates) > 0:
        return gates[0]

    # === Si todas las salidas estan congestionadas, no puede continuar moviendo
    logger.warning("No se ha podido localizar una salida en UIO ni GYE. Todas las salidas se encuentran congestionadas.")
    return None


def find_best_gate_locality(saturada, gye, uio, reference) -> Port:
    logger.info(f"Determinando la mejor salida regional para descongestionar a {saturada.gate}")
    gye = find_good_gate(gye, reference)
    uio = find_good_gate(uio, reference)

    locality = "UIO" if "uio" in saturada.gate else "GYE"
    if locality == "UIO":
        if len(uio) > 0:
            return uio[0]
        else:
            logger.warning("No se ha podido localizar una salida en UIO, buscando salida en GYE")
            if len(gye) > 0:
                return gye[0]  # === Si no encuentra en UIO, busca una salida en GYE
    else:
        if len(gye) > 0:
            return gye[0]
        else:
            logger.warning("No se ha podido localizar una salida en GYE, buscando salida en UIO")
            if len(uio) > 0:
                return uio[0]

    # === Si todas las salidas estan congestionadas, no puede continuar moviendo
    logger.warning("No se ha podido localizar una salida en UIO ni GYE. Todas las salidas se encuentran congestionadas.")
    return None


def find_good_gate(gates, reference):
    good = []
    for gate in gates:
        if gate.available > reference:
            good.append(gate)
    sorted(good, key=lambda item: (item.optimal_available, -item.optimal_priority, item.available), reverse=True)
    return good


def analyze_attributes(best, reference, locality, gates):
    attributes = []
    best_locality = "UIO" if "uio" in best.gate else "GYE"

    if best is None:
        attributes.append({'score': 0, 'attribute': 'No se pudo encontrar una salida apropiada.'})
    else:
        # === Analyze locality
        if best_locality == locality:
            attributes.append({'score': 5, 'attribute': 'La mejor salida se encuentra en la misma region.'})
        else:
            attributes.append({'score': 4, 'attribute': 'La mejor salida se encuentra en otra region.'})

        # === Analyze reference/available
        if best.available >= reference:
            attributes.append(
                {'score': 5, 'attribute': f'La mejor salida tiene capacidad total disponible para cubrir el valor de referencia ({best.available}/{reference}).'})
        else:
            attributes.append(
                {'score': 1, 'attribute': f'La mejor salida no tiene capacidad total disponible para cubrir el valor de referencia ({best.available}/{reference}).'})

        # === Analyze reference/optimal available
        if best.optimal_available >= reference:
            attributes.append({'score': 5,
                               'attribute': f'La mejor salida tiene capacidad commit disponible para cubrir el valor de referencia ({best.optimal_available}/{reference}).'})
        else:
            attributes.append({'score': 3,
                               'attribute': f'La mejor salida no tiene capacidad commit disponible para cubrir el valor de referencia ({best.optimal_available}/{reference}).'})

        # === Analyze priority
        if best.optimal_priority == 0:
            attributes.append({'score': 5, 'attribute': f'La mejor salida tiene 100% de capacidad commit (Prioridad 0).'})
        else:
            attributes.append(
                {'score': 3, 'attribute': f'La mejor salida tiene {best.optimal_thold}% de capacidad commit (Prioridad {best.optimal_priority}).'})

        # === Analyze available capacity ranking
        top = top_position(best, gates)
        if top <= 5:
            attributes.append({'score': 5, 'attribute': f'La mejor salida se encuentra en el puesto {top} de salidas con menor carga.'})
        else:
            attributes.append({'score': 4, 'attribute': f'La mejor salida se encuentra en el puesto {top} de salidas con menor carga.'})
    return attributes


def top_position(best, gates):
    top = sorted(gates, key=lambda x: x.load, reverse=False)
    counter = 1
    for gate in top:
        if gate.gate == best.gate:
            return counter
        counter += 1
    return counter
