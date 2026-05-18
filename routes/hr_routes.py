from flask import Blueprint, redirect, render_template, request, send_file, session, url_for

from services.attendance_service import (
    get_all_attendance_records,
    get_attendance_record,
    get_employee_dashboard_data,
    update_attendance_record,
)
from database import get_users_by_roles
from services.report_service import generate_attendance_report


hr_bp = Blueprint("hr", __name__)


@hr_bp.route("/hr")
def hr_dashboard():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    dashboard_data = get_employee_dashboard_data(session["user_id"])
    all_records = get_all_attendance_records()

    return render_template(
        "hr_dashboard.html",
        own_records=dashboard_data["records"],
        all_records=all_records,
        attendance_percentage=dashboard_data["attendance_percentage"],
        total_days=dashboard_data["total_days"],
        present_days=dashboard_data["present_days"],
    )


@hr_bp.route("/face_registration")
def face_registration():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    users = get_users_by_roles(["hr", "employee"])
    return render_template("face_registration.html", users=users)


@hr_bp.route("/attendance_records")
def attendance_records():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    records = get_all_attendance_records()
    return render_template("attendance_records.html", records=records)


@hr_bp.route("/edit_attendance/<int:id>", methods=["GET", "POST"])
def edit_attendance(id):
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    record = get_attendance_record(id)

    if request.method == "POST":
        update_attendance_record(
            id,
            request.form["check_in"],
            request.form["check_out"],
            request.form["status"],
            session["username"],
            request.form["reason"],
        )

        return redirect(url_for("hr.attendance_records"))

    return render_template("edit_attendance.html", record=record)


@hr_bp.route("/generate_report")
def generate_report():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    report_path = generate_attendance_report()
    return send_file(report_path, as_attachment=True)
