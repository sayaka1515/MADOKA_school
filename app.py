from flask import Flask, render_template, url_for, flash, redirect
from forms import RegistrationForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'madoka_secret_key'

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/location")
def location():
    return render_template('location.html')

@app.route("/news")
def news():
    return render_template('news.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'帳號建立成功：{form.username.data}！', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', title='註冊', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'歡迎回來，{form.email.data}！', 'success')
        return redirect(url_for('home'))
    return render_template('login.html', title='登入', form=form)

if __name__ == '__main__':
    app.run(debug=True)
