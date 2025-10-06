from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

app = Flask(__name__)
app.secret_key = "madoka-secret"  # 表单需要用到 CSRF 防护

# ====== 表单定義 ======
class ContactForm(FlaskForm):
    name = StringField("姓名", validators=[DataRequired(), Length(min=2, max=20)])
    message = TextAreaField("留言內容", validators=[DataRequired(), Length(min=5)])
    submit = SubmitField("送出留言")

# ====== 頁面路由 ======
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/location')
def location():
    return render_template('location.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        flash(f"感謝 {form.name.data} 的留言！內容已收到！", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
