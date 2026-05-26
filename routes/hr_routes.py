from flask import Blueprint, flash, redirect, render_template, request, send_file, session, url_for

from services.attendance_service import (
    get_all_attendance_records,
    get_attendance_record,
    get_employee_dashboard_data,
    get_schedule,
    update_attendance_record,
)
from database import get_users_by_roles
from services.face_service import attach_face_registration_status
from services.report_service import generate_attendance_report


hr_bp = Blueprint("hr", __name__)
ATTENDANCE_EDIT_REASONS = [
    "System missed check-in",
    "System missed check-out",
    "Camera recognition error",
    "Wrong attendance status",
    "Approved manual correction",
]


@hr_bp.route("/hr")
def hr_dashboard():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    dashboard_data = get_employee_dashboard_data(session["user_id"])
    all_records = get_all_attendance_records()

    return render_template(
        "hr/dashboard.html",
        own_records=dashboard_data["records"],
        all_records=all_records,
        attendance_percentage=dashboard_data["attendance_percentage"],
        total_days=dashboard_data["total_days"],
        present_days=dashboard_data["present_days"],
        schedule=get_schedule(),
    )


@hr_bp.route("/face_registration")
def face_registration():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    users = attach_face_registration_status(get_users_by_roles(["hr", "employee"]))
    return render_template("hr/face_registration.html", users=users)


@hr_bp.route("/attendance_records")
def attendance_records():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    records = get_all_attendance_records()
    return render_template("hr/attendance_records.html", records=records)


@hr_bp.route("/edit_attendance/<int:id>", methods=["GET", "POST"])
def edit_attendance(id):
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    record = get_attendance_record(id)

    if request.method == "POST":
        reason = request.form["reason"]

        if reason not in ATTENDANCE_EDIT_REASONS:
            flash("Please select a valid edit reason", "error")
            return render_template(
                "hr/edit_attendance.html",
                record=record,
                edit_reasons=ATTENDANCE_EDIT_REASONS,
            )

        update_attendance_record(
            id,
            request.form["check_in"],
            request.form["check_out"],
            request.form["status"],
            session["system_id"],
            reason,
        )

        return redirect(url_for("hr.attendance_records"))

    return render_template(
        "hr/edit_attendance.html",
        record=record,
        edit_reasons=ATTENDANCE_EDIT_REASONS,
    )


@hr_bp.route("/generate_report")
def generate_report():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    report_path = generate_attendance_report()

    if not report_path:
        flash("No attendance records available. Report was not downloaded.", "error")
        return redirect(url_for("hr.hr_dashboard"))

    return send_file(
        report_path,
        as_attachment=True,
        download_name="all_attendance_report.csv",
    )
