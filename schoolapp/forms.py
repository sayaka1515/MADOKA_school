# ...existing code...
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional
from flask_wtf.file import FileField, FileAllowed

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
    email = StringField('電子郵件', validators=[DataRequired(), Email()])
    submit = SubmitField('寄出重設信')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('新密碼', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('確認密碼', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('重設密碼')
# ...existing code...

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('目前密碼', validators=[DataRequired()])
    new_password = PasswordField('新密碼', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('確認新密碼', validators=[DataRequired(), EqualTo('new_password', message='密碼需一致')])
    submit = SubmitField('變更密碼')

class ChangeEmailForm(FlaskForm):
    new_email = StringField('新電子郵件', validators=[DataRequired(), Email()])
    current_password = PasswordField('目前密碼', validators=[DataRequired()])
    submit = SubmitField('變更電子郵件')
# ...existing code...

class UpdateAccountForm(FlaskForm):
    username = StringField('使用者名稱', validators=[DataRequired(), Length(min=2, max=20)])
    email = EmailField('電子郵件', validators=[DataRequired(), Email()], filters=[normalize_email])
    picture = FileField('上傳大頭照', validators=[FileAllowed(['jpg', 'jpeg', 'png'])])
    submit = SubmitField('更新帳號')
# ...existing code...