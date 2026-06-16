import pandas as pd

from config import REPORT_FILE
from services.attendance_service import get_report_records


def build_report_rows(start_date=None, end_date=None):
    records = get_report_records(start_date, end_date)

    if not records:
        return []

    data = []

    for record in records:
        role_label = "HR Staff" if record["role"] == "hr" else "Employee"
        data.append({
            "Role Order": 1 if record["role"] == "hr" else 2,
            "Group": role_label,
            "Employee ID": record["system_id"],
            "Employee Name": record["full_name"],
            "Department": record["department"],
            "Position": record["position"],
            "Date": record["date"],
            "Check In": record["check_in"] or "-",
            "Check Out": record["check_out"] or "-",
            "Status": record["status"],
            "Overtime": record["overtime"] or "No",
            "Edited By": record["edited_by"] or "-",
            "Edit Reason": record["edit_reason"] or "-",
        })

    return data


def generate_attendance_report(start_date=None, end_date=None):
    return build_report_rows(start_date, end_date)


def export_attendance_report_csv(start_date=None, end_date=None):
    data = build_report_rows(start_date, end_date)

    if not data:
        return None

    df = pd.DataFrame(data)
    df = df.sort_values(["Role Order", "Employee Name", "Date"], ascending=[True, True, False])
    df = df.drop(columns=["Role Order"])
    df.to_csv(REPORT_FILE, index=False)

    return REPORT_FILE
