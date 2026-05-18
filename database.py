import sqlite3
from config import DATABASE


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    required_tables = {"users", "face_profiles", "attendance"}
    existing_tables = {
        row["name"]
        for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    if required_tables.issubset(existing_tables):
        conn.close()
        return

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            department TEXT,
            position TEXT,
            status TEXT DEFAULT 'Active'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS face_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            face_file TEXT NOT NULL,
            registered_by TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            status TEXT DEFAULT 'Present',
            edited_by TEXT,
            edit_reason TEXT
        )
    """)

    conn.commit()
    conn.close()


def seed_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    users = [
        ("superadmin", "123456", "superadmin", "Super Admin", "superadmin@company.com", "Admin", "System Admin"),
        ("hr", "123456", "hr", "HR Manager", "hr@company.com", "Human Resource", "HR Management"),
        ("employee", "123456", "employee", "Employee User", "employee@company.com", "IT", "Software Developer")
    ]

    for user in users:
        existing = cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (user[0],)
        ).fetchone()

        if existing:
            continue

        cursor.execute("""
            INSERT INTO users
            (username, password, role, full_name, email, department, position) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, user)

    conn.commit()
    conn.close()


def find_user_by_credentials(username, password):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    conn.close()
    return user


def get_all_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return users


def get_users_by_roles(roles):
    placeholders = ",".join("?" for _ in roles)
    conn = get_db_connection()
    users = conn.execute(
        f"SELECT * FROM users WHERE role IN ({placeholders})",
        roles
    ).fetchall()
    conn.close()
    return users


def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    return user


def create_user(username, password, role, full_name, email, department, position):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO users
        (username, password, role, full_name, email, department, position)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, password, role, full_name, email, department, position))
    conn.commit()
    conn.close()


def update_user(user_id, username, role, full_name, email, department, position, status):
    conn = get_db_connection()
    conn.execute("""
        UPDATE users
        SET username=?, role=?, full_name=?, email=?, department=?, position=?, status=?
        WHERE id=?
    """, (username, role, full_name, email, department, position, status, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def create_face_profile(user_id, face_file, registered_by):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO face_profiles
        (user_id, face_file, registered_by)
        VALUES (?, ?, ?)
    """, (user_id, face_file, registered_by))
    conn.commit()
    conn.close()
