from flask import Blueprint, redirect, render_template, request, session, url_for

from database import find_user_by_credentials


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = find_user_by_credentials(username, password)

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "superadmin":
                return redirect(url_for("superadmin.superadmin_dashboard"))

            if user["role"] == "hr":
                return redirect(url_for("hr.hr_dashboard"))

            if user["role"] == "employee":
                return redirect(url_for("employee.employee_dashboard"))

        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
