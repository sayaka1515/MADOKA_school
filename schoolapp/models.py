# ...existing code...
from schoolapp import db
from flask_login import UserMixin
from datetime import datetime
from flask import current_app
from itsdangerous import URLSafeTimedSerializer as Serializer

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    profile_image = db.Column(db.String(100), nullable=False, default='default.jpg')  # 新增欄位
    reviews = db.relationship('Review', backref='author', lazy=True)
    def get_reset_token(self, expires_sec=3600):
        s = Serializer(current_app.config.get('SECRET_KEY', 'dev-secret'))
        return s.dumps({'email': self.email})
    
    @staticmethod
    def verify_reset_token(token, max_age=3600):
        s = Serializer(current_app.config.get('SECRET_KEY', 'dev-secret'))
        try:
            data = s.loads(token, max_age=max_age)
        except Exception:
            return None
        return User.query.filter_by(email=data.get('email')).first()
   
class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# ...existing code...