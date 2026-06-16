import time

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from database import (
    delete_user,
    get_all_users,
    get_user_by_id,
    get_users_by_roles,
    get_work_settings,
    insert_user_with_password_hash,
    restore_user,
    update_user,
    update_user_password,
    update_work_settings,
)
from services.attendance_service import clear_attendance_records
from services.face_service import (
    attach_face_registration_status,
    detect_face_from_image_data,
    register_face_from_image_data,
    user_has_face_profile,
)
from services.otp_service import OTP_EXPIRY_SECONDS, generate_otp, send_otp_email
from utils.security import hash_password
from utils.validators import (
    DEPARTMENT_OPTIONS,
    DEPARTMENT_POSITION_OPTIONS,
    POSITION_OPTIONS,
    get_joined_year_options,
    validate_department_position,
    validate_joined_year,
    validate_password,
)


superadmin_bp = Blueprint("superadmin", __name__)
OTP_RESEND_COOLDOWN_SECONDS = 60


@superadmin_bp.route("/superadmin")
def superadmin_dashboard():
    if session.get("role") != "superadmin":
        return redirect(url_for("auth.login"))

    return render_template(
        "superadmin/dashboard.html",
        schedule=get_work_settings()
    )


@superadmin_bp.route("/work_settings", methods=["GET", "POST"])
def work_settings():
    if session.get("role") not in ["superadmin", "hr"]:
        return redirect(url_for("auth.login"))

    message = None

    if request.method == "POST":
        update_work_settings(
            request.form["start_time"],
            request.form["end_time"]
        )
        flash("Work schedule updated successfully", "success")
        return redirect(url_for("superadmin.work_settings"))

    return render_template(
        "shared/work_settings.html",
        schedule=get_work_settings(),
        message=message
    )


@superadmin_bp.route("/clear_attendance", methods=["POST"])
def clear_attendance():
    if session.get("role") != "superadmin":
        return redirect(url_for("auth.login"))

    clear_attendance_records()

    flash("Attendance records cleared successfully", "success")
    return redirect(url_for("superadmin.work_settings"))


@superadmin_bp.route("/employees")
def employees():
    if session.get("role") not in ["superadmin", "hr"]:
        return redirect(url_for("auth.login"))

    users = get_all_users()
    return render_template(
        "superadmin/employees.html",
        users=users,
        can_delete=session.get("role") == "superadmin",
    )


@superadmin_bp.route("/superadmin/face_registration")
def superadmin_face_registration():
    if session.get("role") != "superadmin":
        return redirect(url_for("auth.login"))

    users = attach_face_registration_status(get_users_by_roles(["hr", "employee"]))
    return render_template(
        "hr/face_registration.html",
        users=users,
        page_title="Face Registration",
        page_subtitle="Register or re-register facial profiles for HR and Employee users.",
    )


@superadmin_bp.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    if session.get("role") not in ["superadmin", "hr"]:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        role = request.form["role"]
        joined_year = request.form["joined_year"]
        password = request.form["password"]
        department = request.form["department"]
        position = request.form["position"]

        if role == "superadmin":
            flash("Cannot create another Super Admin account", "error")
            return render_add_employee_form(request.form)

        valid_year, year_error = validate_joined_year(joined_year)
        if not valid_year:
            flash(year_error, "error")
            return render_add_employee_form(request.form)

        valid_password, password_error = validate_password(password)
        if not valid_password:
            flash(password_error, "error")
            return render_add_employee_form(request.form)

        valid_profile, profile_error = validate_department_position(
            role,
            department,
            position,
        )
        if not valid_profile:
            flash(profile_error, "error")
            return render_add_employee_form(request.form)

        email = request.form["email"]
        session["pending_account"] = {
            "password_hash": hash_password(password),
            "role": role,
            "joined_year": joined_year,
            "full_name": request.form["full_name"],
            "email": email,
            "department": department,
            "position": position,
        }

        email_sent, email_message = start_account_creation_otp(email)
        if not email_sent:
            session.pop("pending_account", None)
            flash(email_message, "error")
            return render_add_employee_form(request.form)

        flash("OTP sent to the employee email. Verify OTP to create the account.", "success")
        return redirect(url_for("superadmin.verify_account_otp"))

    return render_add_employee_form()


def render_add_employee_form(form_data=None):
    return render_template(
        "superadmin/add_employee.html",
        years=get_joined_year_options(),
        departments=DEPARTMENT_OPTIONS,
        department_positions=DEPARTMENT_POSITION_OPTIONS,
        positions=POSITION_OPTIONS,
        form_data=form_data or {},
    )


@superadmin_bp.route("/verify_account_otp", methods=["GET", "POST"])
def verify_account_otp():
    if session.get("role") not in ["superadmin", "hr"]:
        return redirect(url_for("auth.login"))

    pending_account = session.get("pending_account")

    if not pending_account:
        flash("No pending account creation request", "error")
        return redirect(url_for("superadmin.add_employee"))

    if request.method == "POST":
        if time.time() > session.get("account_otp_expires_at", 0):
            session.pop("pending_account", None)
            session.pop("account_otp", None)
            session.pop("account_otp_expires_at", None)
            session.pop("account_resend_available_at", None)
            flash("OTP has expired. Please create the account again.", "error")
            return redirect(url_for("superadmin.add_employee"))

        if request.form["otp"] != session.get("account_otp"):
            flash("Wrong OTP. Please try again.", "error")
            return render_template(
                "superadmin/otp_verify.html",
                email=pending_account["email"],
                resend_remaining=get_account_resend_remaining(),
            )

        password_hash = pending_account.get("password_hash") or hash_password(pending_account["password"])
        system_id = insert_user_with_password_hash(
            password_hash,
            pending_account["role"],
            pending_account["joined_year"],
            pending_account["full_name"],
            pending_account["email"],
            pending_account["department"],
            pending_account["position"],
        )

        session.pop("pending_account", None)
        session.pop("account_otp", None)
        session.pop("account_otp_expires_at", None)
        session.pop("account_resend_available_at", None)

        flash(f"Account created successfully. Employee ID: {system_id}", "success")
        return redirect(url_for("superadmin.employees"))

    return render_template(
        "superadmin/otp_verify.html",
        email=pending_account["email"],
        resend_remaining=get_account_resend_remaining(),
    )


@superadmin_bp.route("/resend_account_otp", methods=["POST"])
def resend_account_otp():
    if session.get("role") not in ["superadmin", "hr"]:
        return redirect(url_for("auth.login"))

    pending_account = session.get("pending_account")
    if not pending_account:
        flash("No pending account creation request", "error")
        return redirect(url_for("superadmin.add_employee"))

    remaining = get_account_resend_remaining()
    if remaining > 0:
        flash(f"Please wait {remaining} seconds before requesting another OTP", "error")
        return redirect(url_for("superadmin.verify_account_otp"))

    email_sent, email_message = start_account_creation_otp(pending_account["email"])
    flash(email_message, "success" if email_sent else "error")
    return redirect(url_for("superadmin.verify_account_otp"))


def start_account_creation_otp(email):
    otp = generate_otp()
    email_sent, email_message = send_otp_email(
        email,
        otp,
        "Account Creation"
    )

    if not email_sent:
        return False, email_message

    session["account_otp"] = otp
    session["account_otp_expires_at"] = time.time() + OTP_EXPIRY_SECONDS
    session["account_resend_available_at"] = time.time() + OTP_RESEND_COOLDOWN_SECONDS
    return True, "OTP sent to the employee email"


def get_account_resend_remaining():
    return max(0, int(session.get("account_resend_available_at", 0) - time.time()))


@superadmin_bp.route("/edit_employee/<int:id>", methods=["GET", "POST"])
def edit_employee(id):
    if session.get("role") not in ["superadmin", "hr"]:
        return redirect(url_for("auth.login"))

    user = get_user_by_id(id)

    if not user:
        flash("User not found", "error")
        return redirect(url_for("superadmin.employees"))

    if user["role"] == "superadmin":
        flash("Main Super Admin account cannot be edited", "error")
        return redirect(url_for("superadmin.employees"))

    if user["status"] == "Deleted" or user["deleted_at"]:
        flash("Deleted accounts are read-only", "error")
        return redirect(url_for("superadmin.employees"))

    if request.method == "POST":
        role = request.form["role"]
        new_password = request.form.get("new_password", "").strip()
        department = request.form["department"]
        position = request.form["position"]

        if role == "superadmin":
            flash("Cannot assign Super Admin role", "error")
            return render_edit_employee_form(user)

        if new_password:
            valid_password, password_error = validate_password(new_password)
            if not valid_password:
                flash(password_error, "error")
                return render_edit_employee_form(user)

        valid_profile, profile_error = validate_department_position(
            role,
            department,
            position,
        )
        if not valid_profile:
            flash(profile_error, "error")
            return render_edit_employee_form(user)

        update_user(
            id,
            role,
            request.form["full_name"],
            request.form["email"],
            department,
            position,
            request.form["status"],
        )

        if new_password:
            update_user_password(id, new_password)

        flash("Employee account updated successfully", "success")
        return redirect(url_for("superadmin.employees"))

    return render_edit_employee_form(user)


def render_edit_employee_form(user):
    return render_template(
        "superadmin/edit_employee.html",
        user=user,
        departments=DEPARTMENT_OPTIONS,
        department_positions=DEPARTMENT_POSITION_OPTIONS,
        positions=POSITION_OPTIONS,
    )


@superadmin_bp.route("/delete_employee/<int:id>")
def delete_employee_route(id):
    if session.get("role") != "superadmin":
        return redirect(url_for("auth.login"))

    user = get_user_by_id(id)

    if not user:
        flash("User not found", "error")
        return redirect(url_for("superadmin.employees"))

    if user["role"] == "superadmin":
        flash("Main Super Admin account cannot be deleted", "error")
        return redirect(url_for("superadmin.employees"))

    if user["status"] == "Deleted" or user["deleted_at"]:
        flash("Account is already soft deleted", "error")
        return redirect(url_for("superadmin.employees"))

    delete_user(id)
    flash("Employee account soft deleted successfully", "success")
    return redirect(url_for("superadmin.employees"))


@superadmin_bp.route("/restore_employee/<int:id>", methods=["POST"])
def restore_employee_route(id):
    if session.get("role") != "superadmin":
        return redirect(url_for("auth.login"))

    user = get_user_by_id(id)

    if not user:
        flash("User not found", "error")
        return redirect(url_for("superadmin.employees"))

    if user["role"] == "superadmin":
        flash("Main Super Admin account does not need restore", "error")
        return redirect(url_for("superadmin.employees"))

    if user["status"] != "Deleted" and not user["deleted_at"]:
        flash("Account is already active", "error")
        return redirect(url_for("superadmin.employees"))

    restore_user(id)
    flash("Employee account restored successfully", "success")
    return redirect(url_for("superadmin.employees"))


@superadmin_bp.route("/register_face/<int:user_id>")
def register_face(user_id):
    if session.get("role") not in ["superadmin", "hr"]:
        return redirect(url_for("auth.login"))

    user = get_user_by_id(user_id)

    if not user:
        return "User not found"

    if user["role"] == "superadmin":
        return "Super Admin does not need face registration"

    if user["status"] == "Deleted" or user["deleted_at"]:
        return "Deleted accounts cannot register face profiles"

    return render_template(
        "shared/register_face.html",
        user=user,
        face_registered=user_has_face_profile(user_id),
    )


@superadmin_bp.route("/api/register_face/<int:user_id>", methods=["POST"])
def api_register_face(user_id):
    if session.get("role") not in ["superadmin", "hr"]:
        return jsonify({"success": False, "message": "Please login again"}), 401

    data = request.get_json(silent=True) or {}
    user = get_user_by_id(user_id)

    if not user or user["status"] == "Deleted" or user["deleted_at"]:
        return jsonify({
            "success": False,
            "message": "Deleted accounts cannot register face profiles",
        }), 400

    success, message = register_face_from_image_data(
        user_id,
        data.get("image"),
        session["system_id"],
    )

    return jsonify({
        "success": success,
        "message": message,
    })


@superadmin_bp.route("/api/detect_face", methods=["POST"])
def api_detect_face():
    if session.get("role") not in ["superadmin", "hr"]:
        return jsonify({"success": False, "message": "Please login again"}), 401

    data = request.get_json(silent=True) or {}
    detected, message = detect_face_from_image_data(data.get("image"))

    return jsonify({
        "success": detected,
        "message": message,
    })
