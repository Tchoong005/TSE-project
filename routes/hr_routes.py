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
from services.report_service import export_attendance_report_csv, generate_attendance_report


hr_bp = Blueprint("hr", __name__)
INVALID_EDIT_REASONS = {"none", "n/a", "na", "-", "nil", "null"}


@hr_bp.route("/hr")
def hr_dashboard():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    dashboard_data = get_employee_dashboard_data(session["user_id"])
    report_start_date = session.get("report_start_date", "")
    report_end_date = session.get("report_end_date", "")
    report_rows = []

    if session.get("report_generated"):
        report_rows = generate_attendance_report(report_start_date, report_end_date)

    requested_tab = request.args.get("tab", "hr-self")
    active_tab = "hr-team" if requested_tab == "hr-team" or report_rows else "hr-self"

    return render_template(
        "hr/dashboard.html",
        own_records=dashboard_data["records"],
        attendance_percentage=dashboard_data["attendance_percentage"],
        total_days=dashboard_data["total_days"],
        present_days=dashboard_data["present_days"],
        schedule=get_schedule(),
        report_rows=report_rows,
        report_start_date=report_start_date,
        report_end_date=report_end_date,
        active_tab=active_tab,
    )


@hr_bp.route("/face_registration")
def face_registration():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    users = attach_face_registration_status(get_users_by_roles(["hr", "employee"]))
    return render_template("hr/face_registration.html", users=users)


@hr_bp.route("/attendance_records")
def attendance_records():
    if session.get("role") not in ["hr", "superadmin"]:
        return redirect(url_for("auth.login"))

    records = get_all_attendance_records()
    return render_template("hr/attendance_records.html", records=records)


@hr_bp.route("/edit_attendance/<int:id>", methods=["GET", "POST"])
def edit_attendance(id):
    if session.get("role") not in ["hr", "superadmin"]:
        return redirect(url_for("auth.login"))

    record = get_attendance_record(id)
    can_edit_attendance_fields = session.get("role") == "superadmin"

    if request.method == "POST":
        reason = request.form["reason"].strip()

        if not is_valid_edit_reason(reason):
            flash("Please enter a clear edit reason. Do not use none, n/a, or blank text.", "error")
            return render_template(
                "hr/edit_attendance.html",
                record=record,
                can_edit_attendance_fields=can_edit_attendance_fields,
            )

        check_in = request.form["check_in"] if can_edit_attendance_fields else record["check_in"]
        check_out = request.form["check_out"] if can_edit_attendance_fields else record["check_out"]
        status = request.form["status"] if can_edit_attendance_fields else record["status"]

        update_attendance_record(
            id,
            check_in,
            check_out,
            status,
            session["system_id"],
            reason,
        )

        return redirect(url_for("hr.attendance_records"))

    return render_template(
        "hr/edit_attendance.html",
        record=record,
        can_edit_attendance_fields=can_edit_attendance_fields,
    )


def is_valid_edit_reason(reason):
    normalized = " ".join(reason.lower().split())
    return len(normalized) >= 5 and normalized not in INVALID_EDIT_REASONS


@hr_bp.route("/generate_report", methods=["POST"])
def generate_report():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    start_date = request.form.get("start_date", "")
    end_date = request.form.get("end_date", "")

    if start_date and end_date and end_date < start_date:
        flash("End date cannot be earlier than start date.", "error")
        return redirect(url_for("hr.hr_dashboard", tab="hr-team"))

    report_rows = generate_attendance_report(start_date, end_date)

    if not report_rows:
        flash("No attendance records found for the selected period.", "error")
        return redirect(url_for("hr.hr_dashboard", tab="hr-team"))

    session["report_start_date"] = start_date
    session["report_end_date"] = end_date
    session["export_start_date"] = start_date
    session["export_end_date"] = end_date
    session["report_generated"] = True
    flash("Attendance report generated successfully.", "success")
    return redirect(url_for("hr.hr_dashboard", tab="hr-team"))


@hr_bp.route("/export_csv")
def export_csv():
    if session.get("role") != "hr":
        return redirect(url_for("auth.login"))

    if not session.get("report_generated"):
        flash("Generate a report before exporting CSV.", "error")
        return redirect(url_for("hr.hr_dashboard", tab="hr-team"))

    start_date = session.get("export_start_date")
    end_date = session.get("export_end_date")
    report_path = export_attendance_report_csv(start_date, end_date)

    if not report_path:
        flash("Generate a report with attendance records before exporting CSV.", "error")
        return redirect(url_for("hr.hr_dashboard", tab="hr-team"))

    return send_file(report_path, as_attachment=True, download_name="attendance_report.csv")
