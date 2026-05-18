from flask import Flask

from config import SECRET_KEY
from database import init_db, seed_users
from routes.attendance_routes import attendance_bp
from routes.auth_routes import auth_bp
from routes.employee_routes import employee_bp
from routes.hr_routes import hr_bp
from routes.superadmin_routes import superadmin_bp
from services.face_service import ensure_face_folder


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    ensure_face_folder()
    init_db()
    seed_users()

    app.register_blueprint(attendance_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(superadmin_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(employee_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
