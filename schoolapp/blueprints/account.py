import os
import secrets
from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app as app
from flask_login import login_required, current_user
from PIL import Image
from schoolapp import db, bcrypt
from schoolapp.models import User, Review
from schoolapp.forms import UpdateAccountForm, ChangePasswordForm, ChangeEmailForm

account_bp = Blueprint('account', __name__)

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

        img = Image.open(form_picture)
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        img = img.resize((125, 125), Image.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(picture_path, optimize=True, quality=85)
        app.logger.debug(f"[save_picture] saved -> {picture_path}")
        return picture_fn
    except Exception as e:
        app.logger.error(f"[save_picture] error saving image: {e}")
        return None

@account_bp.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        # 處理圖片上傳
        if getattr(form, 'picture', None) and form.picture.data:
            picture_file = save_picture(form.picture.data)
            if picture_file:
                try:
                    old = getattr(current_user, 'profile_image', None)
                    if old and old != 'default.jpg':
                        old_path = os.path.join(app.root_path, 'static', 'profile_pics', old)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                            app.logger.debug(f"[account] removed old image: {old_path}")
                except Exception as e:
                    app.logger.error(f"[account] error removing old image: {e}")
                current_user.profile_image = picture_file
            else:
                flash('上傳圖片失敗，請檢查檔案格式與大小。', 'warning')

        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip().lower()
        try:
            db.session.commit()
            flash('您的帳號已更新。', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"[account] db commit error: {e}")
            flash('更新失敗，請稍後重試。', 'danger')
        return redirect(url_for('account.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    image_file = url_for('static', filename=f'profile_pics/{getattr(current_user, "profile_image", "default.jpg")}')
    return render_template('account.html', title='帳號', image_file=image_file, form=form)

@account_bp.route("/profile")
@login_required
def profile():
    reviews_q = Review.query.filter_by(user_id=current_user.id).order_by(Review.date_posted.desc()).all()
    return render_template('profile.html', user=current_user, reviews=reviews_q)

@account_bp.route("/change_password", methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not bcrypt.check_password_hash(current_user.password, form.current_password.data):
            flash('目前密碼不正確。', 'danger')
            return redirect(url_for('account.change_password'))
        current_user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
        try:
            db.session.commit()
            flash('密碼已更新。', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"[change_password] db commit error: {e}")
            flash('更新失敗，請稍後重試。', 'danger')
        return redirect(url_for('account.account'))
    return render_template('change_password.html', title='變更密碼', form=form)

@account_bp.route("/change_email", methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        email_norm = form.new_email.data.strip().lower()
        if User.query.filter_by(email=email_norm).first():
            flash('此電子郵件已被使用。', 'warning')
            return redirect(url_for('account.change_email'))
        if not bcrypt.check_password_hash(current_user.password, form.current_password.data):
            flash('目前密碼不正確。', 'danger')
            return redirect(url_for('account.change_email'))
        current_user.email = email_norm
        try:
            db.session.commit()
            flash('電子郵件已更新。', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"[change_email] db commit error: {e}")
            flash('更新失敗，請稍後重試。', 'danger')
        return redirect(url_for('account.account'))
    return render_template('change_email.html', title='變更電子郵件', form=form)