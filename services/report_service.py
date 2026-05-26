import pandas as pd

from config import REPORT_FILE
from services.attendance_service import get_report_records


def generate_attendance_report():
    records = get_report_records()

    if not records:
        return None

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

    df = pd.DataFrame(data)
    df = df.sort_values(["Role Order", "Employee Name", "Date"], ascending=[True, True, False])
    df = df.drop(columns=["Role Order"])
    df.to_csv(REPORT_FILE, index=False)

    return REPORT_FILE
