import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

def create_app():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    template_folder = os.path.join(base_dir, 'templates')
    static_folder = os.path.join(base_dir, 'static')

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    app.config['SECRET_KEY'] = os.environ.get('MADOKA_SECRET', 'madoka_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///madoka.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # 延遲匯入 routes 以避免循環匯入
        try:
            from . import routes  # noqa: F401
        except Exception:
            pass
        db.create_all()

    return app