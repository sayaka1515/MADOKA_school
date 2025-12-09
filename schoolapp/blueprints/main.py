from flask import Blueprint, render_template, session
from flask_login import current_user

main_bp = Blueprint('main', __name__)

def _display_username():
    """回傳應顯示的 username；若 session 資料過期/不存在則清除 session。"""
    if current_user.is_authenticated:
        return current_user.username
    uname = session.get('username')
    if not uname:
        return None
    try:
        from schoolapp.models import User
        u = User.query.filter_by(username=uname).first()
    except Exception:
        u = None
    if u:
        return uname
    session.pop('username', None)
    session.pop('email', None)
    return None

@main_bp.route("/")
@main_bp.route("/home")
def home():
    username = _display_username()
    return render_template('home.html', username=username)

@main_bp.route("/about")
def about():
    username = _display_username()
    return render_template('about.html', username=username)

@main_bp.route("/location")
def location():
    username = _display_username()
    return render_template('location.html', username=username)

@main_bp.route("/news")
def news():
    username = _display_username()
    return render_template('news.html', username=username)