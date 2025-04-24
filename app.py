from flask import Flask, jsonify
import json
import os

app = Flask(__name__)

@app.route('/')
def home():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'scada_config', 'config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)
    return jsonify(config)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
