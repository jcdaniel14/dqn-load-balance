import logging

logger = logging.getLogger('health-monitor')


def find_best_gate(saturada, gye, uio):
    logger.info("Determinando la mejor salida para optimizar")
    gye = sorted(gye, key=lambda item: (item.optimal_priority, -item.available))
    uio = sorted(uio, key=lambda item: (item.optimal_priority, -item.available))

    locality = "UIO" if "uio" in saturada.gate else "GYE"
    if locality == "UIO":
        if len(uio) > 0:
            if uio[0].available > 0:
                return uio[0]
            else:
                logger.warning("No se ha podido localizar una salida en UIO, buscando salida en GYE")
                if len(gye) > 0:
                    if gye[0].available > 0:
                        return gye[0]  # === Si no encuentra en UIO, busca una salida en GYE
        else:
            logger.warning("No se ha podido localizar una salida en UIO, buscando salida en GYE")
            if len(gye) > 0:
                if gye[0].available > 0:
                    return gye[0]  # === Si no encuentra en UIO, busca una salida en GYE
    else:
        if len(gye) > 0:
            if gye[0].available > 0:
                return gye[0]
            else:
                logger.warning("No se ha podido localizar una salida en GYE, buscando salida en UIO")
                if len(uio) > 0:
                    if uio[0].available > 0:
                        return uio[0]
        else:
            logger.warning("No se ha podido localizar una salida en GYE, buscando salida en UIO")
            if len(uio) > 0:
                if uio[0].available > 0:
                    return uio[0]

    # === Si todas las salidas estan congestionadas, no puede continuar moviendo
    logger.warning("No se ha podido localizar una salida en UIO ni GYE. Todas las salidas se encuentran congestionadas.")
    return ""
