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

# Login manager defaults
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

def create_app():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    template_folder = os.path.join(base_dir, 'templates')
    static_folder = os.path.join(base_dir, 'static')

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    # 基本設定：生產環境請用環境變數或設定檔覆寫
    app.config['SECRET_KEY'] = os.environ.get('MADOKA_SECRET', 'madoka_secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///madoka.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mail config (開發可使用本機 Debug SMTP server)
    app.config.update({
        'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.example.com'),
        'MAIL_PORT': int(os.environ.get('MAIL_PORT', 587)),
        'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'true').lower() in ('1','true'),
        'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
        'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    })

    # 初始化 extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # 建議：設定 login_manager.user_loader 在 routes 中或 models 中已實作
    with app.app_context():
        # 延遲匯入以避免循環依賴
        try:
            from . import routes  # noqa: F401
        except Exception:
            pass
        # 建表（開發時方便；生產請改用 migration）
        try:
            db.create_all()
        except Exception:
            # 若資料庫設定錯誤，不要讓應用崩潰在啟動階段
            app.logger.debug("db.create_all() failed on startup")

    return app
# ...existing code...