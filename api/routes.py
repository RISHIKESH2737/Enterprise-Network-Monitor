from flask import Blueprint, jsonify
from flask_login import login_required
from dashboard.monitor import scan_devices


api_bp = Blueprint("api", __name__)


@api_bp.route("/api/status")
@login_required

def api_status():
    return jsonify(scan_devices())