# ...existing code...
from flask import render_template, url_for, flash, redirect, session, request, current_app as app
from schoolapp import db, bcrypt, login_manager
from schoolapp.models import User, Review
from schoolapp.forms import RegistrationForm, LoginForm
from flask_login import login_user, logout_user, current_user, login_required

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@app.route("/home")
def home():
    username = current_user.username if current_user.is_authenticated else session.get('username')
    return render_template('home.html', username=username)

@app.route("/about")
def about():
    username = current_user.username if current_user.is_authenticated else session.get('username')
    return render_template('about.html', username=username)

@app.route("/location")
def location():
    username = current_user.username if current_user.is_authenticated else session.get('username')
    return render_template('location.html', username=username)

@app.route("/news")
def news():
    username = current_user.username if current_user.is_authenticated else session.get('username')
    return render_template('news.html', username=username)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    next_page = request.args.get('next')
    if form.validate_on_submit():
        email_norm = form.email.data.strip().lower()
        if User.query.filter_by(email=email_norm).first():
            flash('此電子郵件已被註冊。', 'warning')
            return render_template('register.html', title='註冊', form=form)
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data.strip(), email=email_norm, password=hashed_pw)
        try:
            db.session.add(user)
            db.session.commit()
            flash('帳號建立成功，請登入！', 'success')
            return redirect(url_for('login', next=next_page)) if next_page else redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print("⚠️ 註冊錯誤：", e)
            flash('註冊失敗，請稍後再試。', 'danger')
    return render_template('register.html', title='註冊', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    next_page = request.args.get('next')
    print("DEBUG: login route enter, validate:", form.validate_on_submit())
    if form.validate_on_submit():
        email_norm = form.email.data.strip().lower()
        user = User.query.filter_by(email=email_norm).first()
        print("DEBUG:", email_norm, "user:", user)
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            session['username'] = user.username
            session['email'] = user.email
            print("DEBUG: login success for", user.username)
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            print("DEBUG: login failed")
            flash('登入失敗，請檢查信箱或密碼', 'danger')
    else:
        if request.method == 'POST':
            print("DEBUG: form.errors =", form.errors)
    return render_template('login.html', title='登入', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash('您已登出。', 'info')
    return redirect(url_for('home'))

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
    # 轉換為模板預期的欄位（templates 使用 r.username）
    reviews = []
    for r in reviews_q:
        author_name = getattr(r, 'author', None)
        if author_name:
            uname = r.author.username
        else:
            uname = session.get('username') or '匿名'
        reviews.append({
            'username': uname,
            'rating': r.rating,
            'comment': r.comment,
            'date_posted': r.date_posted
        })
    return render_template('review.html', reviews=reviews, user=username)

@app.route("/debug_users")
def debug_users():
    users = User.query.all()
    return "<br>".join([f"{u.id} | {u.username} | {u.email}" for u in users]) or "no users"
# ...existing code...