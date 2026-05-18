import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "attendance.db")
FACE_FOLDER = os.path.join(BASE_DIR, "face_data")
REPORT_FILE = os.path.join(BASE_DIR, "attendance_report.csv")
SECRET_KEY = "secret_key"
