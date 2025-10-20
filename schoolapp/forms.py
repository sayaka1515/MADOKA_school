from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

try:
    from wtforms.fields import EmailField
except Exception:
    EmailField = StringField

def normalize_email(value):
    if value:
        return value.strip().lower()
    return value

class RegistrationForm(FlaskForm):
    username = StringField('使用者名稱', validators=[DataRequired(), Length(min=2, max=20)], filters=[lambda v: v.strip() if v else v])
    email = EmailField('電子郵件', validators=[DataRequired(), Email()], filters=[normalize_email])
    password = PasswordField('密碼', validators=[DataRequired()])
    confirm_password = PasswordField('確認密碼', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('註冊')

class LoginForm(FlaskForm):
    email = EmailField('電子郵件', validators=[DataRequired(), Email()], filters=[normalize_email])
    password = PasswordField('密碼', validators=[DataRequired()])
    remember = BooleanField('記住我')
    submit = SubmitField('登入')