from db import get_connection
from decimal import Decimal

def get_network():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM network")
    data = cursor.fetchall()
    fields = [i[0] for i in cursor.description]
    result = [dict(zip(fields, row)) for row in data]
    cursor.close()
    connection.close()
    return result

def get_tests():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM test")
    data = cursor.fetchall()
    fields = [i[0] for i in cursor.description]
    result = [dict(zip(fields,row)) for row in data]
    cursor.close()
    connection.close()
    return result

def save_test(data):
    connection = get_connection()
    cursor = connection.cursor()
    test_id = int(data['test_id'])
    test_name = data['test_name']
    interfaces = data['interfaces']

    if test_id==0:
        cursor.execute("INSERT INTO test (name) VALUES (%s) ", [test_name])
        test_id = connection.insert_id()
        for row in interfaces:
            interface= int(row['interface_id'])
            bw= int(row['bw'])
            cursor.execute("INSERT INTO congestion (interface_id,bw,test_id) VALUES (%s,%s,%s) ",[interface, bw, test_id])
    else:
        cursor.execute("UPDATE test set name=%s where id=%s", (test_name,test_id))
        for row in interfaces:
            interface= int(row['interface_id'])
            bw= int(row['bw'])
            cursor.execute("update congestion set bw=%s where interface_id=%s and test_id=%s ", [bw,interface, test_id])

    connection.commit()
    cursor.close()
    connection.close()
    return test_id


def get_steps_training(set):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM steps_training where test_id=%s",[set])
    data = cursor.fetchall()
    fields = [i[0] for i in cursor.description]
    result = [dict(zip(fields,row)) for row in data]
    cursor.close()
    connection.close()
    return result

def get_test(id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM test_cases where test_id= %s order by `test_id`,`local` desc,`interface`,`interface_id` ",[id])
    data = cursor.fetchall()
    fields = [i[0] for i in cursor.description]
    result = [dict(zip(fields, row)) for row in data]
    cursor.close()
    connection.close()
    return result


def get_congestion(id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT interface_id, congestionado, bw, local,capacidad FROM test_cases where test_id= %s order by `test_id`,`local` desc,`interface`,`interface_id` ",[id])
    data = cursor.fetchall()
    fields = [i[0] for i in cursor.description]
    result = [dict(zip(fields, row)) for row in data]
    cursor.close()
    connection.close()
    return result


