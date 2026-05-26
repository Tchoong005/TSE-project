from flask import Flask

from config import SECRET_KEY
from database import get_user_by_id, init_db, seed_users
from routes.auth_routes import auth_bp
from routes.employee_routes import employee_bp
from routes.hr_routes import hr_bp
from routes.kiosk_routes import kiosk_bp
from routes.profile_routes import profile_bp
from routes.superadmin_routes import superadmin_bp
from services.face_service import ensure_face_folder


def create_app():
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    ensure_face_folder()
    init_db()
    seed_users()

    app.register_blueprint(kiosk_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(superadmin_bp)
    app.register_blueprint(hr_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(profile_bp)

    @app.context_processor
    def inject_current_user():
        from flask import session

        user_id = session.get("user_id")
        return {
            "current_user": get_user_by_id(user_id) if user_id else None
        }

    @app.after_request
    def prevent_authenticated_page_cache(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
