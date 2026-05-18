# Employee Attendance System (EAS)

## IMPORTANT!!!!
pls dont gitpush your .venv

## how to ignore

create a .gitignore in .venv
put * 

## Overview

Employee Attendance System (EAS) is a web-based attendance management system developed using Python Flask. The system is designed to automate employee attendance tracking for organisations by replacing traditional manual attendance methods such as spreadsheets and paper records.

This system uses facial recognition technology for employee check-in and check-out, improving attendance accuracy, reducing administrative workload, and preventing proxy attendance.

The project is developed for Bilobali Sdn. Bhd., an IT services company with approximately 75 employees.

---

## System Objectives

The main objectives of this system are:

- Automate employee attendance check-in and check-out.
- Reduce human errors in attendance recording.
- Prevent proxy attendance using facial recognition.
- Provide attendance monitoring for HR Management.
- Allow Super Admin to manage employees and user roles.
- Allow employees to monitor their own attendance performance.
- Generate attendance reports for management review.

---

## User Roles and Permissions

### 1. Super Admin

The Super Admin is responsible for full system administration.

Permissions:

- Login to the system
- Manage employee accounts
- Add employee records
- Edit employee records
- Delete employee records
- Assign user roles
- Register employee facial profiles
- Access Super Admin dashboard

---

### 2. HR Management

HR Management handles attendance monitoring and correction.

Permissions:

- Login to the system
- View employee attendance records
- Edit attendance records when system errors occur
- Generate attendance reports
- Assist in employee facial registration
- Access HR dashboard

---

### 3. Employee

Employees use the attendance system for daily attendance tracking.

Permissions:

- Login to the system
- Check in using facial recognition
- Check out using facial recognition
- View attendance history
- View attendance percentage
- Access Employee dashboard

---

## System Workflow

### Initial Registration

1. Super Admin or HR Management creates an employee account.
2. A role is assigned to the employee.
3. Employee facial data is registered using the camera.
4. Facial profile is stored for future verification.

---

### Daily Attendance

1. Employee logs into the system.
2. Employee selects Check-In or Check-Out.
3. Camera captures employee face.
4. System compares captured face with registered facial data.
5. If matched:
   - Attendance is recorded automatically.
6. If system recording fails:
   - HR Management manually edits attendance record.

---

## Agile Development Model

This project follows the Agile Software Development Model.

Development is divided into multiple sprints.

### Sprint Plan

| Sprint | Features |
|-------|----------|
| Sprint 1 | Login System + Role-Based Dashboard |
| Sprint 2 | Employee Management + Role Assignment |
| Sprint 3 | Face Registration + Facial Recognition Attendance |
| Sprint 4 | Attendance Monitoring + Attendance Editing |
| Sprint 5 | Attendance Reports + Attendance Percentage |

---

## Technologies Used

Backend:

- Python
- Flask
- SQLite

Frontend:

- HTML
- CSS
- JavaScript

Facial Recognition:

- OpenCV
- face_recognition library

Development Tools:

- Visual Studio Code
- Git
- Python Virtual Environment (venv)

---

## Project Structure

```text
TSE-project/
|
|-- app.py
|-- database.py
|-- config.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|
|-- face_data/
|
|-- templates/
|   |-- login.html
|   |-- superadmin_dashboard.html
|   |-- hr_dashboard.html
|   |-- employee_dashboard.html
|   |-- employees.html
|   |-- add_employee.html
|   |-- edit_employee.html
|   |-- attendance_records.html
|   |-- edit_attendance.html
|
|-- static/
|   |-- style.css
|
|-- routes/
|   |-- __init__.py
|   |-- auth_routes.py
|   |-- superadmin_routes.py
|   |-- hr_routes.py
|   |-- employee_routes.py
|
|-- services/
|   |-- __init__.py
|   |-- face_service.py
|   |-- attendance_service.py
|   |-- report_service.py
```

---

# Installation Guide

## 1. Clone or Download Project

Download the project files or clone the repository.

Example:

```bash
git clone https://github.com/your-repository/TSE-project.git
```

Or manually open the project folder in Visual Studio Code.

---

## 2. Install Python

Make sure Python 3.11 or 3.12 is installed.

Check version:

```bash
python --version
```

Expected output:

```bash
Python 3.x.x
```

---

## 3. Create Virtual Environment

Inside project folder:

```bash
python -m venv .venv
```

This creates a virtual environment folder:

```text
.venv/
```

---

## 4. Activate Virtual Environment

### Windows PowerShell

```powershell
.\.venv\Scripts\activate
```

Successful activation:

```powershell
(.venv)
```

appears in terminal.

---

### Windows CMD

```cmd
.venv\Scripts\activate
```

---

### Mac / Linux

```bash
source .venv/bin/activate
```

---

## 5. Install Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

If pip does not work:

```bash
python -m pip install -r requirements.txt
```

---

## 6. Run Application

Start Flask application:

```bash
python app.py
```

Expected output:

```bash
Running on http://127.0.0.1:5000
```

---

## 7. Open Browser

Visit:

```text
http://127.0.0.1:5000
```

---

# Default Login Accounts

## Super Admin

Username:

superadmin

Password:

123456

---

## HR Management

Username:

hr

Password:

123456

---

## Employee

Username:

employee

Password:

123456

---

# Current Development Status

Current Sprint:

**Sprint 1**

Completed:

- Flask setup
- SQLite database setup
- Login authentication
- Role-based dashboard
- Session management
- Logout

Upcoming:

- Employee CRUD management
- Role assignment
- Facial registration
- Attendance check-in/check-out
- Report generation

---

# Future Enhancements

Planned improvements:

- Real-time facial recognition attendance
- Attendance analytics dashboard
- Export attendance reports (PDF / Excel)
- Payroll integration
- Email notifications
- Mobile-responsive UI

---

# Academic Information

Course:

TSE6223 Software Engineering Fundamentals

Project Title:

Employee Attendance System (EAS)

Institution:

Multimedia University (MMU)

Development Model:

Agile Software Development

