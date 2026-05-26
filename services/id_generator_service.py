from database import build_system_id


def generate_system_id(cursor, joined_year):
    return build_system_id(cursor, joined_year)
