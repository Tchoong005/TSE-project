from datetime import datetime

from database import get_db_connection, get_user_by_id
from services.face_service import match_registered_face_from_image_data, verify_face


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
    conn = get_db_connection()
    conn.execute("""
        UPDATE attendance
        SET check_out=?
        WHERE user_id=? AND date=?
    """, (check_out, user_id, date))
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
    conn = get_db_connection()
    conn.execute("""
        UPDATE attendance
        SET check_in=?, check_out=?, status=?, edited_by=?, edit_reason=?
        WHERE id=?
    """, (check_in, check_out, status, edited_by, reason, record_id))
    conn.commit()
    conn.close()


def get_report_records():
    conn = get_db_connection()
    records = conn.execute("""
        SELECT
            users.full_name,
            users.department,
            attendance.date,
            attendance.check_in,
            attendance.check_out,
            attendance.status
        FROM attendance
        JOIN users ON attendance.user_id = users.id
        ORDER BY attendance.date DESC
    """).fetchall()
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
    }


def record_check_in(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")
    existing = get_attendance_by_user_and_date(user_id, today)

    if existing:
        return False, "You have already checked in today"

    create_check_in(user_id, today, now, "Present")
    return True, "Checked in successfully"


def record_check_out(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M:%S")
    existing = get_attendance_by_user_and_date(user_id, today)

    if not existing:
        return False, "Please check in before checking out"

    if existing["check_out"]:
        return False, "You have already checked out today"

    update_check_out(user_id, today, now)
    return True, "Checked out successfully"


def check_in_employee(user_id):
    user = get_user_by_id(user_id)

    if not user or user["role"] not in ["hr", "employee"]:
        return False, "Only HR and Employee users can check in"

    verified, message = verify_face(user_id)

    if not verified:
        return False, message

    return record_check_in(user_id)


def check_out_employee(user_id):
    user = get_user_by_id(user_id)

    if not user or user["role"] not in ["hr", "employee"]:
        return False, "Only HR and Employee users can check out"

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
