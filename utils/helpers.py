def is_deleted_user(user):
    return bool(user and (user["status"] == "Deleted" or user["deleted_at"]))
