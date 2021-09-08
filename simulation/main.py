from flask import Flask, render_template,json, request
from decimal import Decimal
from qlearning.main import test_model
import model



app = Flask(__name__)

def default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)


"""
Definición controladores web
"""

@app.route('/')
def main():
    interfaces = model.get_network()
    # return render_template('index.html', Interfaces=interfaces)
    return getAllTests()

@app.route('/tests')
def getAllTests():
    tests = model.get_tests()
    return render_template('tests.html', Tests=tests)

@app.route('/newTest')
def newTest():
    NetworkTest = model.get_test(0)
    test_id = 0
    test_name= ""
    return render_template('editTest.html',  **locals() )

@app.route('/editTest/<int:id>')
def editTest(id):
    NetworkTest = model.get_test(id)
    test_id = id
    test_name = NetworkTest[0]['test_name']
    return render_template('editTest.html',  **locals())

@app.route('/saveTest',methods=['POST'])
def saveTest():
    data = request.get_json()
    result = model.save_test(data)
    return json.dumps({'message':'Saved', 'set': result })


@app.route('/test/<int:id>',methods=['get'])
def test(id):
    NetworkTest = model.get_test(id)
    test_id = id
    test_name = NetworkTest[0]['test_name']
    data= test_model(test_id)
    results = json.dumps({"interfaces":NetworkTest , "steps":data},default=default)
    return render_template('resultTest.html',  **locals())

"""
Definición controladores API
"""
@app.route('/congestion/<int:id>',methods=['get'])
def getCongestion(id):
    results = model.get_congestion(id)
    return json.dumps(results ,  default=default)

# Iniciar el servidor
if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)