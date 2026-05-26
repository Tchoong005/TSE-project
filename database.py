import sqlite3
from datetime import datetime

from config import DATABASE
from utils.constants import DELETED_STATUS
from utils.security import hash_password, password_needs_hash, verify_password


DEMO_PASSWORDS = {
    "20050001": "Admin@123",
    "20260002": "Hr@12345",
    "20260003": "Employee@123",
}

_MEMORY_DB_CONNECTION = None


def get_sqlite_target():
    if DATABASE == ":memory:":
        return "file:eas_memory?mode=memory&cache=shared", True

    return DATABASE, DATABASE.startswith("file:")


def get_db_connection():
    global _MEMORY_DB_CONNECTION

    database, use_uri = get_sqlite_target()

    if DATABASE == ":memory:" and _MEMORY_DB_CONNECTION is None:
        _MEMORY_DB_CONNECTION = sqlite3.connect(database, uri=True)
        _MEMORY_DB_CONNECTION.row_factory = sqlite3.Row

    conn = sqlite3.connect(database, uri=use_uri)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            system_id TEXT UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            joined_year TEXT,
            full_name TEXT,
            email TEXT,
            department TEXT,
            position TEXT,
            status TEXT DEFAULT 'Active',
            profile_image TEXT,
            deleted_at TEXT
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
            overtime TEXT DEFAULT 'No',
            edited_by TEXT,
            edit_reason TEXT
        )
    """)

    user_columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(users)").fetchall()
    }

    if "system_id" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN system_id TEXT")

    if "joined_year" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN joined_year TEXT")

    if "profile_image" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_image TEXT")

    if "deleted_at" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN deleted_at TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS work_settings (
            id INTEGER PRIMARY KEY,
            start_time TEXT NOT NULL DEFAULT '08:00',
            end_time TEXT NOT NULL DEFAULT '17:00'
        )
    """)

    attendance_columns = {
        row["name"]
        for row in cursor.execute("PRAGMA table_info(attendance)").fetchall()
    }

    if "overtime" not in attendance_columns:
        cursor.execute("ALTER TABLE attendance ADD COLUMN overtime TEXT DEFAULT 'No'")

    cursor.execute("""
        INSERT OR IGNORE INTO work_settings (id, start_time, end_time)
        VALUES (1, '08:00', '17:00')
    """)

    migrate_system_ids(cursor)
    migrate_demo_profile_values(cursor)
    migrate_password_hashes(cursor)
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_system_id
        ON users(system_id)
    """)

    conn.commit()
    conn.close()


def get_next_sequence(cursor):
    system_ids = cursor.execute("""
        SELECT system_id FROM users
        WHERE system_id IS NOT NULL AND LENGTH(system_id) = 8
    """).fetchall()

    max_sequence = 0

    for row in system_ids:
        suffix = row["system_id"][4:]

        if suffix.isdigit():
            max_sequence = max(max_sequence, int(suffix))

    return max_sequence + 1


def build_system_id(cursor, joined_year):
    sequence = get_next_sequence(cursor)

    while True:
        system_id = f"{joined_year}{sequence:04d}"
        existing = cursor.execute(
            "SELECT id FROM users WHERE system_id = ?",
            (system_id,)
        ).fetchone()

        if not existing:
            return system_id

        sequence += 1


def migrate_system_ids(cursor):
    users = cursor.execute("SELECT * FROM users ORDER BY id").fetchall()
    current_year = str(datetime.now().year)

    for user in users:
        if user["role"] == "superadmin":
            cursor.execute("""
                UPDATE users
                SET system_id = ?, username = ?, joined_year = ?
                WHERE id = ?
            """, ("20050001", "20050001", "2005", user["id"]))
            continue

        if user["system_id"]:
            cursor.execute("""
                UPDATE users
                SET username = ?
                WHERE id = ?
            """, (user["system_id"], user["id"]))

            if not user["joined_year"]:
                cursor.execute("""
                    UPDATE users
                    SET joined_year = ?
                    WHERE id = ?
                """, (user["system_id"][:4], user["id"]))
            continue

        joined_year = user["joined_year"] or current_year
        system_id = build_system_id(cursor, joined_year)
        cursor.execute("""
            UPDATE users
            SET system_id = ?, username = ?, joined_year = ?
            WHERE id = ?
        """, (system_id, system_id, joined_year, user["id"]))

    migrate_demo_passwords(cursor)


def migrate_demo_passwords(cursor):
    for system_id, password in DEMO_PASSWORDS.items():
        cursor.execute("""
            UPDATE users
            SET password = ?
            WHERE system_id = ? AND password IN ('123456', 'Admin@123', 'Hr@12345', 'Employee@123')
        """, (password, system_id))


def migrate_password_hashes(cursor):
    users = cursor.execute("SELECT id, password FROM users").fetchall()

    for user in users:
        if password_needs_hash(user["password"]):
            cursor.execute("""
                UPDATE users
                SET password = ?
                WHERE id = ?
            """, (hash_password(user["password"]), user["id"]))


def migrate_demo_profile_values(cursor):
    cursor.execute("""
        UPDATE users
        SET department = 'Information Technology'
        WHERE department = 'IT'
    """)
    cursor.execute("""
        UPDATE users
        SET department = 'Administration'
        WHERE department = 'Admin'
    """)
    cursor.execute("""
        UPDATE users
        SET position = 'HR Manager'
        WHERE position = 'HR Management'
    """)


def seed_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    users = [
        ("20050001", "20050001", hash_password(DEMO_PASSWORDS["20050001"]), "superadmin", "2005", "Super Admin", "superadmin@company.com", "Admin", "System Admin"),
        ("20260002", "20260002", hash_password(DEMO_PASSWORDS["20260002"]), "hr", "2026", "HR Manager", "hr@company.com", "Human Resource", "HR Manager"),
        ("20260003", "20260003", hash_password(DEMO_PASSWORDS["20260003"]), "employee", "2026", "Employee User", "employee@company.com", "Information Technology", "Software Developer")
    ]

    for user in users:
        existing = cursor.execute(
            "SELECT id FROM users WHERE system_id = ? OR username = ?",
            (user[0], user[1])
        ).fetchone()

        if existing:
            continue

        cursor.execute("""
            INSERT INTO users
            (system_id, username, password, role, joined_year, full_name, email, department, position) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, user)

    conn.commit()
    conn.close()


def find_user_by_credentials(system_id, password):
    conn = get_db_connection()
    user = conn.execute(
        """
        SELECT * FROM users
        WHERE system_id=?
          AND deleted_at IS NULL
          AND COALESCE(status, 'Active') != ?
        """,
        (system_id, DELETED_STATUS)
    ).fetchone()

    if not user or not verify_password(user["password"], password):
        conn.close()
        return None

    if password_needs_hash(user["password"]):
        conn.execute("""
            UPDATE users
            SET password = ?
            WHERE id = ?
        """, (hash_password(password), user["id"]))
        conn.commit()

    conn.close()
    return user


def get_all_users():
    conn = get_db_connection()
    users = conn.execute("""
        SELECT * FROM users
        ORDER BY
            CASE WHEN status = ? OR deleted_at IS NOT NULL THEN 1 ELSE 0 END,
            system_id
    """, (DELETED_STATUS,)).fetchall()
    conn.close()
    return users


def get_users_by_roles(roles):
    placeholders = ",".join("?" for _ in roles)
    conn = get_db_connection()
    users = conn.execute(
        f"""
        SELECT * FROM users
        WHERE role IN ({placeholders})
          AND deleted_at IS NULL
          AND COALESCE(status, 'Active') != ?
        """,
        [*roles, DELETED_STATUS]
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


def get_user_by_email_or_system_id(identifier):
    conn = get_db_connection()
    user = conn.execute("""
        SELECT * FROM users
        WHERE email = ? OR system_id = ?
    """, (identifier, identifier)).fetchone()
    conn.close()
    return user


def get_user_by_system_id(system_id):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE system_id = ?",
        (system_id,)
    ).fetchone()
    conn.close()
    return user


def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute(
        """
        SELECT * FROM users
        WHERE lower(email) = lower(?)
          AND deleted_at IS NULL
          AND COALESCE(status, 'Active') != ?
        """,
        (email, DELETED_STATUS)
    ).fetchone()
    conn.close()
    return user


def insert_user_with_password_hash(password_hash, role, joined_year, full_name, email, department, position):
    conn = get_db_connection()
    cursor = conn.cursor()
    system_id = build_system_id(cursor, joined_year)
    cursor.execute("""
        INSERT INTO users
        (system_id, username, password, role, joined_year, full_name, email, department, position)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (system_id, system_id, password_hash, role, joined_year, full_name, email, department, position))
    conn.commit()
    conn.close()
    return system_id


def create_user(password, role, joined_year, full_name, email, department, position):
    return insert_user_with_password_hash(
        hash_password(password),
        role,
        joined_year,
        full_name,
        email,
        department,
        position,
    )


def update_user(user_id, role, full_name, email, department, position, status):
    conn = get_db_connection()
    conn.execute("""
        UPDATE users
        SET role=?, full_name=?, email=?, department=?, position=?, status=?
        WHERE id=?
    """, (role, full_name, email, department, position, status, user_id))
    conn.commit()
    conn.close()


def update_user_password(user_id, password):
    conn = get_db_connection()
    conn.execute("""
        UPDATE users
        SET password=?
        WHERE id=?
    """, (hash_password(password), user_id))
    conn.commit()
    conn.close()


def update_user_profile_image(user_id, profile_image):
    conn = get_db_connection()
    conn.execute("""
        UPDATE users
        SET profile_image=?
        WHERE id=?
    """, (profile_image, user_id))
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_db_connection()
    conn.execute("""
        UPDATE users
        SET status = ?,
            deleted_at = ?
        WHERE id = ?
    """, (DELETED_STATUS, datetime.now().isoformat(timespec="seconds"), user_id))
    conn.commit()
    conn.close()


def restore_user(user_id):
    conn = get_db_connection()
    conn.execute("""
        UPDATE users
        SET status = 'Active',
            deleted_at = NULL
        WHERE id = ?
    """, (user_id,))
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


def get_latest_face_profiles_by_user():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT user_id, MAX(id) AS latest_id
        FROM face_profiles
        GROUP BY user_id
    """).fetchall()
    conn.close()
    return {row["user_id"]: row["latest_id"] for row in rows}


def get_work_settings():
    conn = get_db_connection()
    settings = conn.execute(
        "SELECT * FROM work_settings WHERE id = 1"
    ).fetchone()
    conn.close()
    return settings


def update_work_settings(start_time, end_time):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO work_settings (id, start_time, end_time)
        VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            start_time = excluded.start_time,
            end_time = excluded.end_time
    """, (start_time, end_time))
    conn.commit()
    conn.close()
