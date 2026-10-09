
from flask import Flask, jsonify
import os

app = Flask(__name__)

VERSION = os.getenv("APP_VERSION", "v1.0")
HEALTH_FAIL = os.getenv("HEALTH_FAIL", "false").lower() == "true"

@app.route("/")
def home():
    return jsonify({
        "application": "LMS",
        "version": VERSION,
        "status": "running"
    })

@app.route("/health")
def health():
    if HEALTH_FAIL:
        return jsonify({"status": "DOWN"}), 500

    return jsonify({
        "status": "UP",
        "version": VERSION
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
