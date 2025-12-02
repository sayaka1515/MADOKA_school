# ...existing code...
from flask import render_template, url_for, flash, redirect, session, request, current_app as app
from schoolapp import db, bcrypt, login_manager, mail
from schoolapp.models import User, Review
from schoolapp.forms import (
    RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, UpdateAccountForm,
    ChangePasswordForm, ChangeEmailForm
)
from flask_login import login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message

import os
import secrets
from PIL import Image

# ---- login manager callbacks ----
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized_callback():
    flash('請先登入以存取該頁面。', 'warning')
    return redirect(url_for('login'))

# ---- helpers ----
def _get_serializer(salt):
    secret = app.config.get('SECRET_KEY') or 'madoka_secret_key'
    return URLSafeTimedSerializer(secret, salt=salt)

def send_verification_link(email):
    s = _get_serializer('email-confirm')
    token = s.dumps(email)
    link = url_for('confirm_email', token=token, _external=True)
    subject = "見瀧原中學 - 驗證您的電子郵件"
    body = f"請點此完成驗證：\n\n{link}\n\n（此郵件由系統自動發出）"
    try:
        msg = Message(subject=subject, recipients=[email], body=body, sender=app.config.get('MAIL_DEFAULT_SENDER'))
        mail.send(msg)
    except Exception as e:
        app.logger.warning(f"[MAIL ERROR] {e}  — fallback to printing link")
        # 開發時輸出連結方便測試
        print(f'[EMAIL] 驗證連結（寄到 {email}）： {link}')
    return token

def send_reset_link(email):
    s = _get_serializer('password-reset')
    token = s.dumps(email)
    link = url_for('reset_token', token=token, _external=True)
    subject = "見瀧原中學 - 密碼重設"
    body = f"若您要求重設密碼，請點此連結：\n\n{link}\n\n若非本人請忽略。"
    try:
        msg = Message(subject=subject, recipients=[email], body=body, sender=app.config.get('MAIL_DEFAULT_SENDER'))
        mail.send(msg)
    except Exception as e:
        app.logger.warning(f"[MAIL ERROR] {e}  — fallback to printing link")
        print(f'[EMAIL] 密碼重設連結（寄到 {email}）： {link}')
    return token

# ...existing code...
def save_picture(form_picture):
    """儲存上傳大頭照：先做中心正方形裁切，再縮放到 125x125，回傳檔名或 None。"""
    if not form_picture:
        return None
    try:
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(getattr(form_picture, 'filename', '') or '')
        f_ext = (f_ext.lower() if f_ext else '.jpg')
        picture_fn = random_hex + f_ext
        picture_dir = os.path.join(app.root_path, 'static', 'profile_pics')
        os.makedirs(picture_dir, exist_ok=True)
        picture_path = os.path.join(picture_dir, picture_fn)

        # 讀取並中心裁切再縮放
        img = Image.open(form_picture)
        # 若有 EXIF 方向可在此處處理 (可選)
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        # 使用 PIL LANCZOS 高品質縮放
        img = img.resize((125, 125), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(picture_path, optimize=True, quality=85)
        app.logger.debug(f"[save_picture] saved -> {picture_path}")
        return picture_fn
    except Exception as e:
        app.logger.error(f"[save_picture] error saving image: {e}")
        return None
# ...existing code...

# ---- routes ----
def _display_username():
    """回傳應顯示的 username；若 session 資料過期/不存在則清除 session。"""
    if current_user.is_authenticated:
        return current_user.username
    uname = session.get('username')
    if not uname:
        return None
    try:
        u = User.query.filter_by(username=uname).first()
    except Exception:
        u = None
    if u:
        return uname
    session.pop('username', None)
    session.pop('email', None)
    return None

@app.route("/")
@app.route("/home")
def home():
    username = _display_username()
    return render_template('home.html', username=username)

@app.route("/about")
def about():
    username = _display_username()
    return render_template('about.html', username=username)

@app.route("/location")
def location():
    username = _display_username()
    return render_template('location.html', username=username)

@app.route("/news")
def news():
    username = _display_username()
    return render_template('news.html', username=username)

@app.route('/resend_verification')
@login_required
def resend_verification():
    if current_user.is_confirmed:
        flash('帳號已驗證。', 'info')
        return redirect(url_for('home'))
    token = send_verification_link(current_user.email)
    if app.debug:
        link = url_for('confirm_email', token=token, _external=True)
        return render_template('dev_verification.html', link=link)
    flash('已重新發送驗證信，請收信（若未收到請檢查垃圾郵件）。', 'info')
    return redirect(url_for('home'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
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
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"register error: {e}")
            flash('註冊失敗，請稍後再試。', 'danger')
    return render_template('register.html', title='註冊', form=form)

@app.route("/confirm_email/<token>")
def confirm_email(token):
    s = _get_serializer('email-confirm')
    try:
        email = s.loads(token, max_age=3600)
    except SignatureExpired:
        flash('驗證連結已過期，請重新註冊或要求重新發送。', 'warning')
        return redirect(url_for('register'))
    except BadSignature:
        flash('驗證連結無效。', 'danger')
        return redirect(url_for('register'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('找不到該使用者。', 'danger')
        return redirect(url_for('register'))
    user.is_confirmed = True
    db.session.commit()
    flash('電子郵件驗證成功，您現在可以登入。', 'success')
    return redirect(url_for('login'))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        email_norm = form.email.data.strip().lower()
        user = User.query.filter_by(email=email_norm).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if not user.is_confirmed:
                flash('請先完成電子郵件驗證。系統已在伺服器輸出驗證連結（開發時用）。', 'warning')
                send_verification_link(user.email)
                return redirect(url_for('login'))
            login_user(user, remember=form.remember.data)
            session['username'] = user.username
            session['email'] = user.email
            flash(f'歡迎回來，{user.username}！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('登入失敗，請檢查信箱或密碼', 'danger')
    else:
        if request.method == 'POST':
            app.logger.debug(f"login form errors: {form.errors}")
    return render_template('login.html', title='登入', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash('您已登出。', 'info')
    return redirect(url_for('home'))

@app.route("/reset_request", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            send_reset_link(user.email)
            flash('已發送重設連結（開發時請看伺服器輸出）。', 'info')
        else:
            # 為避免資訊外洩，不透露 email 是否存在（可改為顯示錯誤）
            flash('已發送重設連結（如有此電子郵件會收到）。', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='重設密碼', form=form)

@app.route("/reset/<token>", methods=['GET', 'POST'])
def reset_token(token):
    s = _get_serializer('password-reset')
    try:
        email = s.loads(token, max_age=3600)
    except SignatureExpired:
        flash('重設連結已過期。', 'warning')
        return redirect(url_for('reset_request'))
    except BadSignature:
        flash('重設連結無效。', 'danger')
        return redirect(url_for('reset_request'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('找不到該使用者。', 'danger')
        return redirect(url_for('reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        db.session.commit()
        flash('密碼已更新，請使用新密碼登入。', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='重設密碼', form=form)

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        # 處理圖片上傳（原有邏輯）
        # ...existing code...

        # 更新其他欄位（保留原有行為）
        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip().lower()

        # 處理密碼變更（若使用者提供 current_password）
        if form.current_password.data:
            if not bcrypt.check_password_hash(current_user.password, form.current_password.data):
                flash('目前密碼不正確，無法變更密碼。', 'danger')
                return redirect(url_for('account'))
            if not form.new_password.data:
                flash('請輸入新密碼。', 'warning')
                return redirect(url_for('account'))
            # 設定新密碼
            current_user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            flash('密碼已更新。', 'success')

        try:
            db.session.commit()
            flash('您的帳號已更新。', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"[account] db commit error: {e}")
            flash('更新失敗，請稍後重試。', 'danger')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    image_file = url_for('static', filename=f'profile_pics/{getattr(current_user, "profile_image", "default.jpg")}')
    return render_template('account.html', title='帳號', image_file=image_file, form=form)
# ...existing code...

@app.route("/profile")
@login_required
def profile():
    reviews_q = Review.query.filter_by(user_id=current_user.id).order_by(Review.date_posted.desc()).all()
    return render_template('profile.html', user=current_user, reviews=reviews_q)

@app.route("/review", methods=['GET', 'POST'])
def review():
    username = current_user.username if current_user.is_authenticated else session.get('username')
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('請先登入再留言！', 'danger')
            return redirect(url_for('login'))
        try:
            rating = int(request.form.get('rating', 0))
        except ValueError:
            flash('評分格式錯誤。', 'danger')
            return redirect(url_for('review'))
        comment = request.form.get('comment', '').strip()
        if not comment:
            flash('留言內容不可為空。', 'warning')
            return redirect(url_for('review'))
        new_review = Review(comment=comment, rating=rating, user_id=current_user.id)
        db.session.add(new_review)
        db.session.commit()
        flash('感謝您的評價！', 'success')
        return redirect(url_for('review'))

    reviews_q = Review.query.order_by(Review.date_posted.desc()).all()
    reviews = []
    for r in reviews_q:
        uname = r.author.username if r.author else '匿名'
        reviews.append({
            'username': uname,
            'rating': r.rating,
            'comment': r.comment,
            'date_posted': r.date_posted
        })
    return render_template('review.html', reviews=reviews, user=username)

@app.route("/change_password", methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not bcrypt.check_password_hash(current_user.password, form.current_password.data):
            flash('目前密碼不正確。', 'danger')
            return redirect(url_for('change_password'))
        current_user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
        try:
            db.session.commit()
            flash('密碼已更新，請使用新密碼登入。', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"[change_password] db commit error: {e}")
            flash('更新失敗，請稍後重試。', 'danger')
        return redirect(url_for('account'))
    return render_template('change_password.html', title='變更密碼', form=form)

@app.route("/change_email", methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        email_norm = form.new_email.data.strip().lower()
        if User.query.filter_by(email=email_norm).first():
            flash('此電子郵件已被使用。', 'warning')
            return redirect(url_for('change_email'))
        if not bcrypt.check_password_hash(current_user.password, form.current_password.data):
            flash('目前密碼不正確。', 'danger')
            return redirect(url_for('change_email'))
        current_user.email = email_norm
        try:
            db.session.commit()
            flash('電子郵件已更新。', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"[change_email] db commit error: {e}")
            flash('更新失敗，請稍後重試。', 'danger')
        return redirect(url_for('account'))
    return render_template('change_email.html', title='變更電子郵件', form=form)
# ...existing code...

@app.route("/debug_users")
def debug_users():
    users = User.query.all()
    return "<br>".join([f"{u.id} | {u.username} | {u.email} | confirmed={u.is_confirmed} | profile_image={getattr(u,'profile_image',None)}" for u in users]) or "no users"
# ...existing code...