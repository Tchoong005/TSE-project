from flask import Blueprint, redirect, render_template, request, session, url_for

from database import create_user, delete_user, get_all_users, get_user_by_id, update_user
from services.face_service import register_face as register_face_service


superadmin_bp = Blueprint("superadmin", __name__)


@superadmin_bp.route("/superadmin")
def superadmin_dashboard():
    if session.get("role") != "superadmin":
        return redirect(url_for("auth.login"))

    return render_template("superadmin_dashboard.html")


@superadmin_bp.route("/employees")
def employees():
    if session.get("role") != "superadmin":
        return redirect(url_for("auth.login"))

    users = get_all_users()
    return render_template("employees.html", users=users)


@superadmin_bp.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    if session.get("role") != "superadmin":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        role = request.form["role"]

        if role == "superadmin":
            return "Cannot create another Super Admin account"

        create_user(
            request.form["username"],
            request.form["password"],
            role,
            request.form["full_name"],
            request.form["email"],
            request.form["department"],
            request.form["position"],
        )

        return redirect(url_for("superadmin.employees"))

    return render_template("add_employee.html")


@superadmin_bp.route("/edit_employee/<int:id>", methods=["GET", "POST"])
def edit_employee(id):
    if session.get("role") != "superadmin":
        return redirect(url_for("auth.login"))

    user = get_user_by_id(id)

    if not user:
        return "User not found"

    if user["role"] == "superadmin":
        return "Main Super Admin account cannot be edited"

    if request.method == "POST":
        role = request.form["role"]

        if role == "superadmin":
            return "Cannot assign Super Admin role"

        update_user(
            id,
            request.form["username"],
            role,
            request.form["full_name"],
            request.form["email"],
            request.form["department"],
            request.form["position"],
            request.form["status"],
        )

        return redirect(url_for("superadmin.employees"))

    return render_template("edit_employee.html", user=user)


@superadmin_bp.route("/delete_employee/<int:id>")
def delete_employee_route(id):
    if session.get("role") != "superadmin":
        return redirect(url_for("auth.login"))

    user = get_user_by_id(id)

    if not user:
        return "User not found"

    if user["role"] == "superadmin":
        return "Main Super Admin account cannot be deleted"

    delete_user(id)
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

    success, message = register_face_service(user_id, session["username"])

    if not success:
        return message

    if session.get("role") == "hr":
        return redirect(url_for("hr.face_registration"))

    return redirect(url_for("superadmin.employees"))
