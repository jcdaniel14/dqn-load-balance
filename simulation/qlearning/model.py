import numpy as np
import pymysql
from decimal import Decimal
import json

def get_connection():
    return pymysql.connect(host='localhost', user='root', password='root', db='tesis')

def default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)


def get_congestion(id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT interface_id, congestionado, bw, local,capacidad FROM test_cases where test_id= %s order by `test_id`,`local` desc,`interface`,`interface_id` ",[id])
    data = cursor.fetchall()
    fields = [i[0] for i in cursor.description]
    result = [dict(zip(fields, row)) for row in data]
    result = np.array(list(map(lambda x : {"interface_id":x["interface_id"],  "congestionado": bool(x["congestionado"]), "bw":int(x['bw']), "local": x["local"] , "capacidad": x["capacidad"]}, result)))
    cursor.close()
    connection.close()
    return result
