# ...existing code...
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()

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

    # Mail config (use environment vars in production)
    app.config.update({
        'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.example.com'),
        'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
        'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'true').lower() in ('1','true'),
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    })

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    with app.app_context():
        # 延遲匯入 routes 以避免循環匯入
        try:
            from . import routes  # noqa: F401
        except Exception:
            pass
        db.create_all()

    return app
# ...existing code...