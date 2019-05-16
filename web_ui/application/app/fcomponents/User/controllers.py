from flask import Blueprint, redirect, render_template, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext
from wtforms import StringField, PasswordField, validators
from app.fcomponents.User.models import UserModel
from werkzeug.security import check_password_hash
import app.fcomponents.Common as Common

module = Blueprint("User", __name__, url_prefix="/user")


class LoginForm(FlaskForm):
    username = StringField(lazy_gettext("Username:"), [validators.DataRequired(), validators.Length(max=255)])
    password = PasswordField(lazy_gettext("Password:"), [validators.DataRequired(), validators.Length(max=255)])


@module.route("/login", methods=Common.http_methods)
def login():
    logout_user()
    form = LoginForm()
    if form.validate_on_submit():
        user = UserModel.load(username=form.username.data)

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("index"))
        Common.flash_message(_("Wrong username or password"))

    return render_template("login.html", form=form, title=_("Login"))


@module.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@module.route("/change_locale/<locale>")
@login_required
def change_locale(locale):
    current_user.change_locale(locale)
    return redirect(url_for("index"))
