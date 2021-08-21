import sys
from database import get_pass, get_mysql_db
from log import init_logger

sys.path.append('/home/gsantiago/2021/app/netflow/manage_automove')
from loader import handle_session, advertised_route
from utils import reduced_port, edit_prefix, get_actual_prefixes

logger = init_logger('test-move', file=False)


# def test_is_advertised_route():
#     prefix = "181.199.54.0/24"
#     router = "rointernetuio1"
#     port = "Bundle-Ether90"
#     logger.info(f"Validando una subred que esta entre las advertised-routes. ({prefix} - {router}:{port})")
#     session = handle_session(router, get_pass())
#     conn = get_mysql_db(db='proveedores')
#     cursor = conn.cursor()
#     assert advertised_route(port, prefix, session, cursor) is True
#     logger.info(f"Subred {prefix} encontrada entre las advertised-routes")
#     if conn:
#         conn.close()
#     session.disconnect()


# def test_is_hw_advertised_route():
#     prefix = "157.100.74.0/24"
#     router = "rointernetgye2"
#     port = "Eth-Trunk196"
#     logger.info(f"Validando una subred que esta entre las advertised-routes [HW]. ({prefix} - {router}:{port})")
#     session = handle_session(router, get_pass())
#     conn = get_mysql_db(db='proveedores')
#     cursor = conn.cursor()
#     assert advertised_route(port, prefix, 3, session, cursor) is True
#     logger.info(f"Subred {prefix} no ha sido encontrada entre las advertised-routes")
#     if conn:
#         conn.close()
#     session.disconnect()

# def test_insert_px():
#     logger.info("Insertando ip en prefix-list")
#     destination_port = "Eth-Trunk196"
#     prefix = "192.168.2.1/32"
#     alt_prefix = "192.168.2.1 32"
#     router = "rointernetgye2"
#     session = handle_session(router, get_pass())
#     prefix_set = f"NETDEV-ANUNCIO_AUTO_{reduced_port(destination_port)}"
#     edit_prefix(prefix_set, "add", prefix, 3, session)
#
#     pxs = get_actual_prefixes(prefix_set, session)
#     is_in = alt_prefix in pxs
#     assert is_in is True
#     session.disconnect()


def test_delete_px():
    logger.info("Eliminando ip en prefix-list")
    destination_port = "Eth-Trunk196"
    prefix = "192.168.1.1/32"
    alt_prefix = "192.168.1.1 32"
    router = "rointernetgye2"
    session = handle_session(router, get_pass())
    prefix_set = f"NETDEV-ANUNCIO_AUTO_{reduced_port(destination_port)}"
    edit_prefix(prefix_set, "remove", prefix, 3, session)

    pxs = get_actual_prefixes(prefix_set, session)
    is_in = alt_prefix in pxs
    assert is_in is False
    session.disconnect()

# def test_check_px():
#     logger.info("Insertando ip en prefix-list")
#     destination_port = "Eth-Trunk196"
#     router = "rointernetgye2"
#     session = handle_session(router, get_pass())
#     pxs = get_actual_prefixes(prefix_set, session)
#     for line in pxs:
#         logger.info(pxs)
#     assert True is True
#     session.disconnect()
