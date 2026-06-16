import time

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from database import get_user_by_email, get_user_by_id, update_user_password
from services.auth_service import authenticate_user, get_login_error
from services.otp_service import OTP_EXPIRY_SECONDS, generate_otp, send_otp_email
from utils.validators import validate_password


auth_bp = Blueprint("auth", __name__)
OTP_RESEND_COOLDOWN_SECONDS = 60


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        system_id = request.form["system_id"]
        password = request.form["password"]
        user = authenticate_user(system_id, password)

        if user:
            session["user_id"] = user["id"]
            session["system_id"] = user["system_id"]
            session["role"] = user["role"]
            flash("Login successful", "success")

            if user["role"] == "superadmin":
                return redirect(url_for("superadmin.superadmin_dashboard"))

            if user["role"] == "hr":
                return redirect(url_for("hr.hr_dashboard"))

            if user["role"] == "employee":
                return redirect(url_for("employee.employee_dashboard"))

        else:
            flash(get_login_error(system_id, password), "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        user = get_user_by_email(email)

        if not user:
            flash("No account found for that email", "error")
            return render_template("auth/forgot_password.html")

        if not user["email"]:
            flash("This account does not have a registered email", "error")
            return render_template("auth/forgot_password.html")

        email_sent, email_message = start_forgot_password_otp(user)
        if not email_sent:
            flash(email_message, "error")
            return render_template("auth/forgot_password.html")

        flash("OTP sent to your registered email", "success")
        return redirect(url_for("auth.verify_forgot_otp"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/verify_forgot_otp", methods=["GET", "POST"])
def verify_forgot_otp():
    if not session.get("forgot_user_id"):
        flash("Start forgot password first", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        if time.time() > session.get("forgot_otp_expires_at", 0):
            clear_forgot_password_session()
            flash("OTP has expired. Please request a new OTP.", "error")
            return redirect(url_for("auth.forgot_password"))

        if request.form["otp"] != session.get("forgot_otp"):
            flash("Wrong OTP. Please try again.", "error")
            return render_template(
                "auth/otp_verify.html",
                email=session.get("forgot_email"),
                resend_remaining=get_forgot_resend_remaining(),
            )

        session["forgot_otp_verified"] = True
        flash("OTP verified. Set your new password.", "success")
        return redirect(url_for("auth.reset_password"))

    return render_template(
        "auth/otp_verify.html",
        email=session.get("forgot_email"),
        resend_remaining=get_forgot_resend_remaining(),
    )


@auth_bp.route("/resend_forgot_otp", methods=["POST"])
def resend_forgot_otp():
    if not session.get("forgot_user_id"):
        flash("Start forgot password first", "error")
        return redirect(url_for("auth.forgot_password"))

    remaining = get_forgot_resend_remaining()
    if remaining > 0:
        flash(f"Please wait {remaining} seconds before requesting another OTP", "error")
        return redirect(url_for("auth.verify_forgot_otp"))

    user = get_user_by_id(session["forgot_user_id"])
    if not user:
        clear_forgot_password_session()
        flash("Account not found. Please start again.", "error")
        return redirect(url_for("auth.forgot_password"))

    email_sent, email_message = start_forgot_password_otp(user)
    flash(email_message, "success" if email_sent else "error")
    return redirect(url_for("auth.verify_forgot_otp"))


@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if not session.get("forgot_user_id") or not session.get("forgot_otp_verified"):
        flash("Verify OTP before resetting password", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return render_template("auth/reset_password.html")

        valid_password, password_error = validate_password(password)
        if not valid_password:
            flash(password_error, "error")
            return render_template("auth/reset_password.html")

        update_user_password(session["forgot_user_id"], password)
        clear_forgot_password_session()
        flash("Password reset successfully. Please login with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html")


def clear_forgot_password_session():
    session.pop("forgot_user_id", None)
    session.pop("forgot_email", None)
    session.pop("forgot_otp", None)
    session.pop("forgot_otp_expires_at", None)
    session.pop("forgot_otp_verified", None)
    session.pop("forgot_resend_available_at", None)


def start_forgot_password_otp(user):
    otp = generate_otp()
    email_sent, email_message = send_otp_email(
        user["email"],
        otp,
        "Password Reset"
    )

    if not email_sent:
        return False, email_message

    session["forgot_user_id"] = user["id"]
    session["forgot_email"] = user["email"]
    session["forgot_otp"] = otp
    session["forgot_otp_expires_at"] = time.time() + OTP_EXPIRY_SECONDS
    session["forgot_resend_available_at"] = time.time() + OTP_RESEND_COOLDOWN_SECONDS
    return True, "OTP sent to your registered email"


def get_forgot_resend_remaining():
    return max(0, int(session.get("forgot_resend_available_at", 0) - time.time()))
