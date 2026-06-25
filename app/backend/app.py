from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS
import pandas as pd
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "app"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

try:
    from app.backend.routes.APImeteo import meteo_bp
except ModuleNotFoundError:
    from backend.routes.APImeteo import meteo_bp


app = Flask(__name__)
CORS(app)  # autorise React a appeler l'API

# ==== import des routes ====
app.register_blueprint(meteo_bp, url_prefix='/api/meteo')



@app.route("/api/status")
def status():
    return jsonify({
        "status": "ok"
    })


@app.route("/api/routes")
def routes():
    return jsonify({
        "routes": [str(rule) for rule in app.url_map.iter_rules()]
    })


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5001)
