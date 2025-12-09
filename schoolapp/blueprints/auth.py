from flask import Blueprint, render_template, url_for, flash, redirect, session, request, current_app as app
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message
from schoolapp import db, bcrypt, mail
from schoolapp.models import User
from schoolapp.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm

auth_bp = Blueprint('auth', __name__)

def _get_serializer(salt):
    secret = app.config.get('SECRET_KEY') or 'madoka_secret_key'
    return URLSafeTimedSerializer(secret, salt=salt)

def send_verification_link(email):
    s = _get_serializer('email-confirm')
    token = s.dumps(email)
    link = url_for('auth.confirm_email', token=token, _external=True)
    subject = "見瀧原中學 - 驗證您的電子郵件"
    body = f"請點此完成驗證：\n\n{link}\n\n（此郵件由系統自動發出）"
    try:
        msg = Message(subject=subject, recipients=[email], body=body, sender=app.config.get('MAIL_DEFAULT_SENDER'))
        mail.send(msg)
    except Exception as e:
        app.logger.warning(f"[MAIL ERROR] {e}  — fallback to printing link")
        print(f'[EMAIL] 驗證連結（寄到 {email}）： {link}')
    return token

def send_reset_link(email):
    s = _get_serializer('password-reset')
    token = s.dumps(email)
    link = url_for('auth.reset_token', token=token, _external=True)
    subject = "見瀧原中學 - 密碼重設"
    body = f"若您要求重設密碼，請點此連結：\n\n{link}\n\n若非本人請忽略。"
    try:
        msg = Message(subject=subject, recipients=[email], body=body, sender=app.config.get('MAIL_DEFAULT_SENDER'))
        mail.send(msg)
    except Exception as e:
        app.logger.warning(f"[MAIL ERROR] {e}  — fallback to printing link")
        print(f'[EMAIL] 密碼重設連結（寄到 {email}）： {link}')
    return token

@auth_bp.route('/resend_verification')
@login_required
def resend_verification():
    if current_user.is_confirmed:
        flash('帳號已驗證。', 'info')
        return redirect(url_for('main.home'))
    token = send_verification_link(current_user.email)
    if app.debug:
        link = url_for('auth.confirm_email', token=token, _external=True)
        return render_template('dev_verification.html', link=link)
    flash('已重新發送驗證信，請收信（若未收到請檢查垃圾郵件）。', 'info')
    return redirect(url_for('main.home'))

@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        email_norm = form.email.data.strip().lower()
        if User.query.filter_by(email=email_norm).first():
            flash('此電子郵件已被註冊。', 'warning')
            return render_template('register.html', title='註冊', form=form)
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data.strip(), email=email_norm, password=hashed_pw, is_confirmed=False)
        try:
            db.session.add(user)
            db.session.commit()
            send_verification_link(user.email)
            flash('註冊成功，請檢查電子郵件完成驗證（開發時請看伺服器輸出）。', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"register error: {e}")
            flash('註冊失敗，請稍後再試。', 'danger')
    return render_template('register.html', title='註冊', form=form)

@auth_bp.route("/confirm_email/<token>")
def confirm_email(token):
    s = _get_serializer('email-confirm')
    try:
        email = s.loads(token, max_age=3600)
    except SignatureExpired:
        flash('驗證連結已過期，請重新註冊或要求重新發送。', 'warning')
        return redirect(url_for('auth.register'))
    except BadSignature:
        flash('驗證連結無效。', 'danger')
        return redirect(url_for('auth.register'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('找不到該使用者。', 'danger')
        return redirect(url_for('auth.register'))
    user.is_confirmed = True
    db.session.commit()
    flash('電子郵件驗證成功，您現在可以登入。', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        email_norm = form.email.data.strip().lower()
        user = User.query.filter_by(email=email_norm).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if not user.is_confirmed:
                flash('請先完成電子郵件驗證。系統已在伺服器輸出驗證連結（開發時用）。', 'warning')
                send_verification_link(user.email)
                return redirect(url_for('auth.login'))
            login_user(user, remember=form.remember.data)
            session['username'] = user.username
            session['email'] = user.email
            flash(f'歡迎回來，{user.username}！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('登入失敗，請檢查信箱或密碼', 'danger')
    else:
        if request.method == 'POST':
            app.logger.debug(f"login form errors: {form.errors}")
    return render_template('login.html', title='登入', form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash('您已登出。', 'info')
    return redirect(url_for('main.home'))

@auth_bp.route("/reset_request", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            send_reset_link(user.email)
            flash('已發送重設連結（開發時請看伺服器輸出）。', 'info')
        else:
            flash('已發送重設連結（如有此電子郵件會收到）。', 'info')
        return redirect(url_for('auth.login'))
    return render_template('reset_request.html', title='重設密碼', form=form)

@auth_bp.route("/reset/<token>", methods=['GET', 'POST'])
def reset_token(token):
    s = _get_serializer('password-reset')
    try:
        email = s.loads(token, max_age=3600)
    except SignatureExpired:
        flash('重設連結已過期。', 'warning')
        return redirect(url_for('auth.reset_request'))
    except BadSignature:
        flash('重設連結無效。', 'danger')
        return redirect(url_for('auth.reset_request'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('找不到該使用者。', 'danger')
        return redirect(url_for('auth.reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.session.commit()
        flash('密碼已更新，請使用新密碼登入。', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_token.html', title='重設密碼', form=form)