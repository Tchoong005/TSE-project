import os
import uuid

from werkzeug.utils import secure_filename


ALLOWED_PROFILE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def is_allowed_profile_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PROFILE_EXTENSIONS


def save_profile_image(image, user_id, app_root_path):
    if not image or not image.filename:
        return None, "Choose an image before uploading"

    if not is_allowed_profile_image(image.filename):
        return None, "Profile image must be PNG, JPG, JPEG, or WEBP"

    filename = secure_filename(image.filename)
    extension = filename.rsplit(".", 1)[1].lower()
    image_name = f"user_{user_id}_{uuid.uuid4().hex}.{extension}"
    upload_folder = os.path.join(app_root_path, "static", "images", "profile_images")
    os.makedirs(upload_folder, exist_ok=True)
    image.save(os.path.join(upload_folder, image_name))
    return f"images/profile_images/{image_name}", None
