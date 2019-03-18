from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators


class LoginForm(FlaskForm):
    username = StringField("Username:", [validators.DataRequired(), validators.Length(max=255)])
    password = PasswordField("Password:", [validators.DataRequired(), validators.Length(max=255)])

