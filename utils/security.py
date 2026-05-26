from hmac import compare_digest

from werkzeug.security import check_password_hash, generate_password_hash


PASSWORD_HASH_PREFIXES = ("scrypt:", "pbkdf2:", "argon2:")


def password_needs_hash(password):
    return not password.startswith(PASSWORD_HASH_PREFIXES)


def hash_password(password):
    return generate_password_hash(password)


def verify_password(stored_password, password):
    if not stored_password:
        return False

    if password_needs_hash(stored_password):
        return compare_digest(stored_password, password)

    return check_password_hash(stored_password, password)
