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

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_name=None):
    """應用工廠函式"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from config import config
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    # 載入設定
    app.config.from_object(config.get(config_name, config['default']))
    
    # 初始化 extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from schoolapp.models import User
        return User.query.get(int(user_id))

    with app.app_context():
        # 匯入並註冊 Blueprint
        from schoolapp.blueprints.main import main_bp
        from schoolapp.blueprints.auth import auth_bp
        from schoolapp.blueprints.account import account_bp
        from schoolapp.blueprints.review import review_bp
        
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(account_bp)
        app.register_blueprint(review_bp)
        
        # 建立資料庫表
        try:
            from . import models  # noqa: F401
            db.create_all()
        except Exception as e:
            app.logger.debug(f"db.create_all() error: {e}")

    return app