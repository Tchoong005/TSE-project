from datetime import datetime

from database import get_db_connection, get_user_by_id, get_work_settings
from services.face_service import match_registered_face_from_image_data, verify_face


def get_schedule():
    settings = get_work_settings()

    if not settings:
        return {
            "start_time": "08:00",
            "end_time": "17:00",
        }

    return {
        "start_time": settings["start_time"],
        "end_time": settings["end_time"],
    }


def time_to_minutes(value):
    if not value:
        return None

    parts = value.split(":")
    return (int(parts[0]) * 60) + int(parts[1])


def is_late(check_in, start_time):
    check_in_minutes = time_to_minutes(check_in)
    start_minutes = time_to_minutes(start_time)
    return check_in_minutes is not None and start_minutes is not None and check_in_minutes > start_minutes


def is_overtime(check_out, end_time):
    check_out_minutes = time_to_minutes(check_out)
    end_minutes = time_to_minutes(end_time)
    return check_out_minutes is not None and end_minutes is not None and check_out_minutes > end_minutes


def get_employee_attendance(user_id):
    conn = get_db_connection()
    records = conn.execute("""
        SELECT * FROM attendance
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,)).fetchall()
    conn.close()
    return records


def count_present_days(user_id):
    conn = get_db_connection()
    count = conn.execute("""
        SELECT COUNT(*) AS count
        FROM attendance
        WHERE user_id = ? AND status IN ('Present', 'Late')
    """, (user_id,)).fetchone()["count"]
    conn.close()
    return count


def get_attendance_by_user_and_date(user_id, date):
    conn = get_db_connection()
    record = conn.execute(
        "SELECT * FROM attendance WHERE user_id=? AND date=?",
        (user_id, date)
    ).fetchone()
    conn.close()
    return record


def create_check_in(user_id, date, check_in, status="Present"):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO attendance (user_id, date, check_in, status)
        VALUES (?, ?, ?, ?)
    """, (user_id, date, check_in, status))
    conn.commit()
    conn.close()


def update_check_out(user_id, date, check_out):
    schedule = get_schedule()
    overtime = "Yes" if is_overtime(check_out, schedule["end_time"]) else "No"
    conn = get_db_connection()
    conn.execute("""
        UPDATE attendance
        SET check_out=?, overtime=?
        WHERE user_id=? AND date=?
    """, (check_out, overtime, user_id, date))
    conn.commit()
    conn.close()


def get_all_attendance_records():
    conn = get_db_connection()
    records = conn.execute("""
        SELECT attendance.*, users.full_name
        FROM attendance
        JOIN users ON attendance.user_id = users.id
        ORDER BY attendance.date DESC
    """).fetchall()
    conn.close()
    return records


def get_attendance_record(record_id):
    conn = get_db_connection()
    record = conn.execute("""
        SELECT attendance.*, users.full_name
        FROM attendance
        JOIN users ON attendance.user_id = users.id
        WHERE attendance.id = ?
    """, (record_id,)).fetchone()
    conn.close()
    return record


def update_attendance_record(record_id, check_in, check_out, status, edited_by, reason):
    schedule = get_schedule()
    overtime = "Yes" if is_overtime(check_out, schedule["end_time"]) else "No"
    conn = get_db_connection()
    conn.execute("""
        UPDATE attendance
        SET check_in=?, check_out=?, status=?, overtime=?, edited_by=?, edit_reason=?
        WHERE id=?
    """, (check_in, check_out, status, overtime, edited_by, reason, record_id))
    conn.commit()
    conn.close()


def clear_attendance_records():
    conn = get_db_connection()
    conn.execute("DELETE FROM attendance")
    conn.commit()
    conn.close()


def get_report_records(start_date=None, end_date=None):
    conn = get_db_connection()
    filters = ["users.role IN ('hr', 'employee')"]
    params = []

    if start_date:
        filters.append("attendance.date >= ?")
        params.append(start_date)

    if end_date:
        filters.append("attendance.date <= ?")
        params.append(end_date)

    where_clause = " AND ".join(filters)
    records = conn.execute(f"""
        SELECT
            users.system_id,
            users.full_name,
            users.role,
            users.department,
            users.position,
            attendance.date,
            attendance.check_in,
            attendance.check_out,
            attendance.status,
            attendance.overtime,
            attendance.edited_by,
            attendance.edit_reason
        FROM attendance
        JOIN users ON attendance.user_id = users.id
        WHERE {where_clause}
        ORDER BY users.role DESC, users.full_name, attendance.date DESC
    """, params).fetchall()
    conn.close()
    return records


def get_employee_dashboard_data(user_id):
    records = get_employee_attendance(user_id)
    total_days = len(records)
    present_days = count_present_days(user_id)

    if total_days > 0:
        attendance_percentage = round((present_days / total_days) * 100, 2)
    else:
        attendance_percentage = 0

    return {
        "records": records,
        "attendance_percentage": attendance_percentage,
        "total_days": total_days,
        "present_days": present_days,
        "schedule": get_schedule(),
    }


def record_check_in(user_id):
    user = get_user_by_id(user_id)

    if not user or user["role"] not in ["hr", "employee"]:
        return False, "Only HR and Employee users can use attendance"

    if user["status"] == "Deleted" or user["deleted_at"]:
        return False, "Deleted accounts cannot use attendance"

    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")
    existing = get_attendance_by_user_and_date(user_id, today)

    if existing:
        return False, "You have already checked in today"

    schedule = get_schedule()
    status = "Late" if is_late(now, schedule["start_time"]) else "Present"

    create_check_in(user_id, today, now, status)

    if status == "Late":
        return True, "Checked in successfully - Late"

    return True, "Checked in successfully"


def record_check_out(user_id):
    user = get_user_by_id(user_id)

    if not user or user["role"] not in ["hr", "employee"]:
        return False, "Only HR and Employee users can use attendance"

    if user["status"] == "Deleted" or user["deleted_at"]:
        return False, "Deleted accounts cannot use attendance"

    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")
    existing = get_attendance_by_user_and_date(user_id, today)

    if not existing:
        return False, "Please check in before checking out"

    if existing["check_out"]:
        return False, "You have already checked out today"

    update_check_out(user_id, today, now)
    schedule = get_schedule()

    if is_overtime(now, schedule["end_time"]):
        return True, "Checked out successfully - Overtime"

    return True, "Checked out successfully"


def record_auto_attendance(user_id):
    schedule = get_schedule()
    now = datetime.now().strftime("%H:%M:%S")

    if time_to_minutes(now) >= time_to_minutes(schedule["end_time"]):
        success, message = record_check_out(user_id)
        return success, message, "Check Out"

    today = datetime.now().strftime("%Y-%m-%d")
    existing = get_attendance_by_user_and_date(user_id, today)

    if existing:
        return False, "You have already checked in today", "Check In"

    success, message = record_check_in(user_id)
    return success, message, "Check In"


def check_in_employee(user_id):
    user = get_user_by_id(user_id)

    if not user or user["role"] not in ["hr", "employee"]:
        return False, "Only HR and Employee users can check in"

    if user["status"] == "Deleted" or user["deleted_at"]:
        return False, "Deleted accounts cannot check in"

    verified, message = verify_face(user_id)

    if not verified:
        return False, message

    return record_check_in(user_id)


def check_out_employee(user_id):
    user = get_user_by_id(user_id)

    if not user or user["role"] not in ["hr", "employee"]:
        return False, "Only HR and Employee users can check out"

    if user["status"] == "Deleted" or user["deleted_at"]:
        return False, "Deleted accounts cannot check out"

    verified, message = verify_face(user_id)

    if not verified:
        return False, message

    return record_check_out(user_id)


def kiosk_check_in(image_data):
    user, message = match_registered_face_from_image_data(image_data)

    if not user:
        return False, message, None

    success, attendance_message = record_check_in(user["id"])
    return success, attendance_message, user


def kiosk_check_out(image_data):
    user, message = match_registered_face_from_image_data(image_data)

    if not user:
        return False, message, None

    success, attendance_message = record_check_out(user["id"])
    return success, attendance_message, user


def kiosk_scan(image_data, mode=None):
    if mode not in [None, "", "auto", "check_in", "check_out"]:
        return {
            "success": False,
            "status": "error",
            "message": "Invalid attendance mode",
        }

    if mode == "check_in":
        success, message, user = kiosk_check_in(image_data)
        action = "Check In"
    elif mode == "check_out":
        success, message, user = kiosk_check_out(image_data)
        action = "Check Out"
    else:
        user, message = match_registered_face_from_image_data(image_data)

        if not user:
            return {
                "success": False,
                "status": "error",
                "message": message,
            }

        success, message, action = record_auto_attendance(user["id"])

    status = "success" if success else "error"

    if not success and message in [
        "You have already checked in today",
        "You have already checked out today",
        "Please check in before checking out",
        "Attendance already completed today",
    ]:
        status = "warning"

    response = {
        "success": success,
        "status": status,
        "action": action,
        "message": message,
    }

    if user:
        response["employee_name"] = user["full_name"]

    return response
