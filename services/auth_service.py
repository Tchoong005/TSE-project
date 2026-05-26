from database import find_user_by_credentials, get_user_by_system_id
from utils.constants import DELETED_STATUS
from utils.security import verify_password


def authenticate_user(system_id, password):
    return find_user_by_credentials(system_id, password)


def get_login_error(system_id, password):
    user = get_user_by_system_id(system_id)

    if not user:
        return "Invalid employee ID or password"

    if user["status"] == DELETED_STATUS or user["deleted_at"]:
        return "This account has been deleted. Please contact the administrator."

    if not verify_password(user["password"], password):
        return "Invalid employee ID or password"

    return "Unable to login. Please contact the administrator."
