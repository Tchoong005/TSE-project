import random
import smtplib
from email.message import EmailMessage

from config import MAIL_PASSWORD, MAIL_SMTP_HOST, MAIL_SMTP_PORT, MAIL_USERNAME
from utils.constants import OTP_EXPIRY_SECONDS


def generate_otp():
    return f"{random.randint(0, 999999):06d}"


def send_otp_email(recipient, otp, purpose):
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        return False, "Email OTP is not configured. Add MAIL_USERNAME and MAIL_PASSWORD to .env, then restart Flask."

    message = EmailMessage()
    message["Subject"] = f"Employee Attendance System OTP - {purpose}"
    message["From"] = MAIL_USERNAME
    message["To"] = recipient
    message.set_content(
        f"Your OTP is {otp}.\n\n"
        "This code will expire in 5 minutes.\n"
        "If you did not request this code, please ignore this email."
    )

    try:
        with smtplib.SMTP_SSL(MAIL_SMTP_HOST, MAIL_SMTP_PORT) as smtp:
            smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
            smtp.send_message(message)
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail login failed. Use a Gmail App Password, not your normal Gmail password."
    except smtplib.SMTPException as error:
        return False, f"OTP email could not be sent: {error}"
    except OSError as error:
        return False, f"Unable to connect to Gmail SMTP: {error}"

    return True, "OTP email sent successfully"
