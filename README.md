# Employee Attendance System (EAS)

Employee Attendance System (EAS) is a Flask-based attendance management system for Bilobali Sdn. Bhd. It uses role-based dashboards, email OTP account flows, and face recognition for attendance check-in/check-out.

## Current Features

- Employee ID login with role-based dashboard routing.
- Three dashboard roles: Super Admin, HR Staff, and Employee.
- Email OTP for account creation and forgot password reset.
- Passwords are stored as hashes, not plaintext.
- Employee account soft delete and restore. Deleted accounts remain visible in Employee Management, cannot login, and can be restored by Super Admin.
- Website-based face registration using the browser camera.
- Face-recognition attendance kiosk.
- HR attendance review, attendance correction, work schedule settings, and CSV report generation.
- Profile page with user-uploaded profile photo.
- Collapsible sidebar with profile and logout grouped at the bottom.

## Roles

| Role | Dashboard | Main Access |
| --- | --- | --- |
| Super Admin | `/superadmin` | Manage employee accounts, assign roles, register faces, set work schedule |
| HR Staff | `/hr` | View/correct attendance, register faces, generate reports, set work schedule |
| Employee | `/employee` | View personal attendance summary and history |

## Account Rules

- Users login with Employee ID, not username.
- `Role` controls dashboard access.
- `Department` and `Position` describe the employee profile.
- HR Staff accounts must be in the Human Resource department.
- Joined year options are generated automatically from 2005 through 5 years after the current year. For example, in 2026 the form includes up to 2031, so 2027 and 2028 employees can be added without changing code.
- Delete is a soft delete: the row stays in the employee table with status `Deleted` and `deleted_at`.
- Super Admin can restore a soft-deleted account from Employee Management.

## Security Notes

- Passwords are hashed with Werkzeug password hashing before storage.
- Existing plaintext passwords are migrated to hashes when the app initializes.
- Deleted accounts are blocked from login and face/attendance workflows.
- Email OTP requires mail environment variables. See `.env` or your shell environment for:

```text
MAIL_USERNAME
MAIL_PASSWORD
```

## Default Login Accounts

| Role | Employee ID | Password |
| --- | --- | --- |
| Super Admin | `20050001` | `Admin@123` |
| HR Staff | `20260002` | `Hr@12345` |
| Employee | `20260003` | `Employee@123` |

## Installation

### Required Versions

Use Python 3.10 64-bit for the most reliable setup. This project uses face recognition packages, and those packages can fail on newer Python versions such as 3.12 or 3.13 on Windows.

Download links:

- Python 3.10.11: open `https://www.python.org/downloads/release/python-31011/`, scroll to Files, click `Windows installer (64-bit)`.
- Visual Studio Code: open `https://code.visualstudio.com/Download`, click `Windows`.
- Git for Windows, if you need Git commands: open `https://git-scm.com/download/win`, then run the downloaded installer.

During Python installation, tick `Add python.exe to PATH`.

### VS Code Setup

Open this project folder in VS Code:

```text
File -> Open Folder -> TSE-project
```

Create the virtual environment in VS Code's terminal:

```powershell
py -3.10 -m venv .venv
```

Select the project interpreter in VS Code:

```text
Ctrl + Shift + P -> Python: Select Interpreter -> .venv\Scripts\python.exe
```

Open a new VS Code terminal. It should show `(.venv)` at the left side of the prompt. If it does not activate automatically, run:

```powershell
.\.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

If that fails, try these commands in order:

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt
```

If face recognition packages still fail on Windows, install the binary package first, then retry requirements:

```powershell
pip install dlib-bin
pip install face-recognition-models
pip install face-recognition
pip install -r requirements.txt
```

Run the app:

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

### Environment Variables

Do not hardcode passwords or secrets in Python files. The app automatically reads a local `.env` file, and `.env` is ignored by Git.

Create `.env` from the example file:

```powershell
copy .env.example .env
```

Open `.env` and fill in your own values:

```text
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_16_character_gmail_app_password
EAS_SECRET_KEY=change-this-to-a-long-random-secret
```

For Gmail, `MAIL_PASSWORD` must be a Gmail App Password, not your normal Gmail login password.

To create a Gmail App Password:

1. Open `https://myaccount.google.com/security`
2. Turn on `2-Step Verification`
3. Open `https://myaccount.google.com/apppasswords`
4. Create an app password for this Flask project
5. Copy the 16-character password into `.env`

After changing `.env`, stop Flask and start it again:

```powershell
python app.py
```

You can also set the variables directly in PowerShell instead of using `.env`:

```powershell
$env:MAIL_USERNAME="your_email@gmail.com"
$env:MAIL_PASSWORD="your_gmail_app_password"
$env:EAS_SECRET_KEY="change-this-to-a-long-random-secret"
python app.py
```

To use a different SQLite database for testing:

```powershell
$env:EAS_DATABASE="C:\tmp\eas_test.db"
python app.py
```

## Project Structure

```text
TSE-project/
|-- app.py
|-- config.py
|-- database.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- attendance.db
|-- face_data/
|-- routes/
|   |-- auth_routes.py
|   |-- employee_routes.py
|   |-- hr_routes.py
|   |-- kiosk_routes.py
|   |-- profile_routes.py
|   |-- superadmin_routes.py
|-- services/
|   |-- attendance_service.py
|   |-- auth_service.py
|   |-- face_service.py
|   |-- id_generator_service.py
|   |-- otp_service.py
|   |-- profile_service.py
|   |-- report_service.py
|-- models/
|   |-- attendance_model.py
|   |-- otp_model.py
|   |-- user_model.py
|-- utils/
|   |-- constants.py
|   |-- helpers.py
|   |-- security.py
|   |-- validators.py
|-- static/
|   |-- css/
|   |   |-- auth.css
|   |   |-- dashboard.css
|   |   |-- kiosk.css
|   |   |-- main.css
|   |-- images/
|   |   |-- bilobali_logo.png
|   |-- js/
|   |   |-- account_form.js
|   |   |-- app_shell.js
|   |   |-- attendance.js
|   |   |-- kiosk_camera.js
|   |   |-- profile.js
|-- templates/
|   |-- auth/
|   |   |-- forgot_password.html
|   |   |-- login.html
|   |   |-- otp_verify.html
|   |   |-- reset_password.html
|   |-- employee/
|   |   |-- attendance_history.html
|   |   |-- dashboard.html
|   |-- hr/
|   |   |-- attendance_records.html
|   |   |-- dashboard.html
|   |   |-- edit_attendance.html
|   |   |-- face_registration.html
|   |-- kiosk/
|   |   |-- attendance_kiosk.html
|   |-- shared/
|   |   |-- modal.html
|   |   |-- navbar.html
|   |   |-- profile.html
|   |   |-- register_face.html
|   |   |-- settings.html
|   |   |-- sidebar.html
|   |   |-- toast.html
|   |   |-- work_settings.html
|   |-- superadmin/
|   |   |-- add_employee.html
|   |   |-- dashboard.html
|   |   |-- edit_employee.html
|   |   |-- employees.html
|   |   |-- otp_verify.html
```

## Development Notes

- `.gitignore` excludes `.venv/`, `.env`, `attendance.db`, face profile `.pkl` files, generated reports, and uploaded profile images.
- CSS is split by responsibility:
  - `static/css/main.css`: global variables, base elements, and shared controls.
  - `static/css/auth.css`: login, forgot password, OTP, reset password, and auth responsive rules.
  - `static/css/dashboard.css`: sidebar, dashboard cards, tables, forms, profile, settings, face registration, and dashboard responsive rules.
  - `static/css/kiosk.css`: attendance kiosk camera page and kiosk responsive rules.
- `attendance.db` is a local SQLite database and may change during local testing.
