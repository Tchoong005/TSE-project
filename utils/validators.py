import re
from datetime import datetime


DEPARTMENT_POSITION_OPTIONS = {
    "Human Resource": [
        "HR Manager",
        "HR Executive",
        "HR Assistant",
    ],
    "Information Technology": [
        "Software Developer",
        "System Analyst",
        "IT Support",
        "QA Tester",
    ],
    "Finance": [
        "Finance Manager",
        "Finance Executive",
        "Account Assistant",
    ],
    "Operations": [
        "Operations Manager",
        "Operations Executive",
        "Operations Assistant",
    ],
    "Sales & Marketing": [
        "Sales Manager",
        "Sales Executive",
        "Marketing Executive",
    ],
    "Administration": [
        "Admin Manager",
        "Admin Executive",
        "Office Assistant",
    ],
}


DEPARTMENT_OPTIONS = list(DEPARTMENT_POSITION_OPTIONS.keys())
POSITION_OPTIONS = [
    position
    for positions in DEPARTMENT_POSITION_OPTIONS.values()
    for position in positions
]


def get_joined_year_options(start_year=2005, future_years=5):
    current_year = datetime.now().year
    end_year = current_year + future_years
    return list(range(end_year, start_year - 1, -1))


def validate_joined_year(joined_year):
    if not joined_year or not re.fullmatch(r"\d{4}", joined_year):
        return False, "Joined year must be exactly 4 digits"

    year = int(joined_year)
    current_year = datetime.now().year

    if year > current_year + 5:
        return False, "Joined year cannot be more than 5 years in the future"

    if year < 2005:
        return False, "Joined year cannot be earlier than 2005"

    return True, None


def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not re.search(r"[A-Za-z]", password):
        return False, "Password must include at least one letter"

    if not re.search(r"\d", password):
        return False, "Password must include at least one number"

    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "Password must include at least one symbol"

    return True, None


def validate_department_position(role, department, position):
    if department not in DEPARTMENT_POSITION_OPTIONS:
        return False, "Please select a valid department"

    if position not in DEPARTMENT_POSITION_OPTIONS[department]:
        return False, "Please select a valid position for the selected department"

    if role == "hr" and department != "Human Resource":
        return False, "HR Staff role must use the Human Resource department"

    return True, None
