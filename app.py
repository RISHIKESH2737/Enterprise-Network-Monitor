from flask import Flask
from flask_socketio import SocketIO
from database.db import db, init_db
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from settings.routes import settings_bp
from flask_login import LoginManager
from auth.models import User
import os

socketio = SocketIO(async_mode="threading")
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)

    # Fixed secret key — won't log users out on restart
    # In production, set this as an environment variable:
    # export SECRET_KEY="your-long-random-string"
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-production-abc123xyz")

    app.config["SQLALCHEMY_DATABASE_URI"] = \
        "sqlite:///" + os.path.join(BASE_DIR, "network_monitor.db")

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    # Blueprints — api routes are now inside dashboard_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(settings_bp)

    init_db(app)

    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


app = create_app()


if __name__ == "__main__":
    socketio.run(app, debug=True)