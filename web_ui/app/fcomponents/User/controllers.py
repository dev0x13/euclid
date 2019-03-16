from flask import Blueprint, redirect, render_template, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.fcomponents.User.forms import LoginForm
from app.fcomponents.User.models import UserModel
from werkzeug.security import check_password_hash
import app.fcomponents.Helpers as Helpers

module = Blueprint("User", __name__, url_prefix="/user")


@module.route("/login", methods=Helpers.methods)
def login():
    logout_user()
    form = LoginForm()
    if form.validate_on_submit():
        user = UserModel().load(username=form.username.data)
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for("index"))
        Helpers.flash_message("Wrong username or password")
    return render_template("login.html", form=form, title="Login")


@module.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
