from flask import Blueprint, redirect, render_template, session, url_for

from services.attendance_service import get_employee_dashboard_data


employee_bp = Blueprint("employee", __name__)


@employee_bp.route("/employee")
def employee_dashboard():
    if session.get("role") != "employee":
        return redirect(url_for("auth.login"))

    dashboard_data = get_employee_dashboard_data(session["user_id"])
    return render_template("employee/dashboard.html", **dashboard_data)


@employee_bp.route("/check_in")
def check_in():
    return redirect(url_for("kiosk.attendance_kiosk"))


@employee_bp.route("/check_out")
def check_out():
    return redirect(url_for("kiosk.attendance_kiosk"))
