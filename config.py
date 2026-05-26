import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def load_env_file(path=os.path.join(BASE_DIR, ".env")):
    if not os.path.exists(path):
        return

    with open(path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


load_env_file()

DATABASE = os.environ.get("EAS_DATABASE", os.path.join(BASE_DIR, "attendance.db"))
FACE_FOLDER = os.path.join(BASE_DIR, "face_data")
REPORT_FILE = os.path.join(BASE_DIR, "attendance_report.csv")
SECRET_KEY = os.environ.get("EAS_SECRET_KEY", "dev-only-change-this-secret")
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "").replace(" ", "") or None
MAIL_SMTP_HOST = os.environ.get("MAIL_SMTP_HOST", "smtp.gmail.com")
MAIL_SMTP_PORT = int(os.environ.get("MAIL_SMTP_PORT", "465"))
