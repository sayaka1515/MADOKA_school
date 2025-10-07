from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('使用者名稱', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('電子郵件', validators=[DataRequired(), Email()])
    password = PasswordField('密碼', validators=[DataRequired()])
    confirm_password = PasswordField('確認密碼', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('註冊')

class LoginForm(FlaskForm):
    email = StringField('電子郵件', validators=[DataRequired(), Email()])
    password = PasswordField('密碼', validators=[DataRequired()])
    remember = BooleanField('記住我')
    submit = SubmitField('登入')
