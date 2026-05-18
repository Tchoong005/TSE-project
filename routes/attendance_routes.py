from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from services.attendance_service import kiosk_check_in, kiosk_check_out


attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/")
def home():
    return render_template("attendance_kiosk.html")


@attendance_bp.route("/attendance_kiosk")
def attendance_kiosk():
    return render_template("attendance_kiosk.html")


@attendance_bp.route("/kiosk_check_in")
def kiosk_check_in_route():
    return redirect(url_for("attendance.attendance_kiosk"))


@attendance_bp.route("/kiosk_check_out")
def kiosk_check_out_route():
    return redirect(url_for("attendance.attendance_kiosk"))


@attendance_bp.route("/api/kiosk_check_in", methods=["POST"])
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


@attendance_bp.route("/api/kiosk_check_out", methods=["POST"])
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
