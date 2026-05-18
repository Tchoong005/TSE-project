import pandas as pd

from config import REPORT_FILE
from services.attendance_service import get_report_records


def generate_attendance_report():
    records = get_report_records()
    data = []

    for record in records:
        data.append({
            "Employee Name": record["full_name"],
            "Department": record["department"],
            "Date": record["date"],
            "Check In": record["check_in"],
            "Check Out": record["check_out"],
            "Status": record["status"],
        })

    df = pd.DataFrame(data)
    df.to_csv(REPORT_FILE, index=False)

    return REPORT_FILE
