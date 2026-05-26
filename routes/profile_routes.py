from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from database import get_user_by_id, update_user_password, update_user_profile_image
from services.profile_service import save_profile_image
from utils.security import verify_password
from utils.validators import validate_password


profile_bp = Blueprint("profile", __name__)


def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    return get_user_by_id(user_id)


@profile_bp.route("/profile", methods=["GET", "POST"])
def profile():
    user = get_current_user()

    if not user:
        flash("Please login to view your profile", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        profile_image, error = save_profile_image(
            request.files.get("profile_image"),
            user["id"],
            current_app.root_path,
        )

        if error:
            flash(error, "error")
            return redirect(url_for("profile.profile"))

        update_user_profile_image(user["id"], profile_image)
        flash("Profile photo updated", "success")
        return redirect(url_for("profile.profile"))

    return render_template(
        "shared/profile.html",
        user=user,
    )


@profile_bp.route("/settings", methods=["GET", "POST"])
def settings():
    user = get_current_user()

    if not user:
        flash("Please login to update your settings", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not verify_password(user["password"], old_password):
            flash("Old password is incorrect", "error")
            return render_template("shared/settings.html", user=user)

        if new_password != confirm_password:
            flash("New password and confirm password do not match", "error")
            return render_template("shared/settings.html", user=user)

        valid_password, password_error = validate_password(new_password)
        if not valid_password:
            flash(password_error, "error")
            return render_template("shared/settings.html", user=user)

        update_user_password(user["id"], new_password)
        flash("Password updated successfully. Use the new password on your next login.", "success")
        return redirect(url_for("profile.settings"))

    return render_template("shared/settings.html", user=user)
