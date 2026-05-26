from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from services.attendance_service import get_schedule, kiosk_check_in, kiosk_check_out, kiosk_scan


kiosk_bp = Blueprint("kiosk", __name__)


@kiosk_bp.route("/")
def home():
    return render_template("kiosk/attendance_kiosk.html", schedule=get_schedule())


@kiosk_bp.route("/attendance_kiosk")
def attendance_kiosk():
    return render_template("kiosk/attendance_kiosk.html", schedule=get_schedule())


@kiosk_bp.route("/kiosk_check_in")
def kiosk_check_in_route():
    return redirect(url_for("kiosk.attendance_kiosk"))


@kiosk_bp.route("/kiosk_check_out")
def kiosk_check_out_route():
    return redirect(url_for("kiosk.attendance_kiosk"))


@kiosk_bp.route("/api/kiosk_check_in", methods=["POST"])
def api_kiosk_check_in():
    data = request.get_json(silent=True) or {}
    success, message, user = kiosk_check_in(data.get("image"))

    response = {
        "success": success,
        "message": message,
    }

    if user:
        response["employee_name"] = user["full_name"]

    return jsonify(response)


@kiosk_bp.route("/api/kiosk_check_out", methods=["POST"])
def api_kiosk_check_out():
    data = request.get_json(silent=True) or {}
    success, message, user = kiosk_check_out(data.get("image"))

    response = {
        "success": success,
        "message": message,
    }

    if user:
        response["employee_name"] = user["full_name"]

    return jsonify(response)


@kiosk_bp.route("/api/kiosk_scan", methods=["POST"])
def api_kiosk_scan():
    data = request.get_json(silent=True) or {}
    response = kiosk_scan(data.get("image"), data.get("mode"))
    return jsonify(response)
