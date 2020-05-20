from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.route('/data')
def hello_world():
    """Example Api
    """
    return jsonify({'data':[1,2,3,4,5,6,7,8,9,10]})

@app.route('/')
def hello(name=None):
    return render_template('index.html')

if __name__ == '__main__':
    app.run()