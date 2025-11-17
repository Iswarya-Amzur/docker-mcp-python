from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "service": "backend"})

@app.route('/api/data')  
def get_data():
    return jsonify({"message": "Hello from backend!", "data": [1, 2, 3, 4, 5]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)