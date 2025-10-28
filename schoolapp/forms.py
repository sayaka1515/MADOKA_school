from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
import re

try:
    from wtforms.fields import EmailField
except Exception:
    EmailField = StringField

def normalize_email(value):
    if value:
        return value.strip().lower()
    return value

def validate_password_strength(form, field):
    pw = field.data or ''
    if len(pw) < 8 or not re.search(r'\d', pw) or not re.search(r'[A-Za-z]', pw):
        raise ValidationError('密碼需至少 8 碼，並包含英文字母與數字。')

class RegistrationForm(FlaskForm):
    username = StringField('使用者名稱', validators=[DataRequired(), Length(min=2, max=20)])
    email = EmailField('電子郵件', validators=[DataRequired(), Email()], filters=[normalize_email])
    password = PasswordField('密碼', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('確認密碼', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('註冊')

class LoginForm(FlaskForm):
    email = EmailField('電子郵件', validators=[DataRequired(), Email()], filters=[normalize_email])
    password = PasswordField('密碼', validators=[DataRequired()])
    remember = BooleanField('記住我')
    submit = SubmitField('登入')

class RequestResetForm(FlaskForm):
    email = EmailField('電子郵件', validators=[DataRequired(), Email()], filters=[normalize_email])
    submit = SubmitField('發送重設連結')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('新密碼', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('確認新密碼', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('重設密碼')