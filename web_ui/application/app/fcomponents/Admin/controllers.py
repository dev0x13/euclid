import uuid

from bson import ObjectId
from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, validators, PasswordField
from app.fcomponents import Common
from app.fcomponents.Common import ModelFactory
from app.fcomponents.User.models import UserModel
from flask_babel import _, lazy_gettext


from werkzeug.security import generate_password_hash

module = Blueprint("Admin", __name__, url_prefix="/admin")


class AppModel(ModelFactory.produce("apps", ["key", "title", "creator_id"])):
    def save(self):
        if self.title == "":
            raise ValueError(_("Invalid title"))

        super().save()

    @classmethod
    def load_all(cls):
        inst = super().load_all()

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_id))

        return inst


class AppForm(FlaskForm):
    title = StringField([validators.DataRequired()], render_kw={"placeholder": lazy_gettext("Title")})


class UserForm(FlaskForm):
    username = StringField([validators.DataRequired()], render_kw={"placeholder": lazy_gettext("Username")})
    email = StringField([validators.DataRequired()], render_kw={"placeholder": lazy_gettext("Email")})
    password = PasswordField(render_kw={"placeholder": lazy_gettext("Password")})
    repeat_password = PasswordField(render_kw={"placeholder": lazy_gettext("Repeat password")})

    # Actions

    is_admin = BooleanField(lazy_gettext('Is admin'))
    manage_parsers = BooleanField(lazy_gettext('Can manage parsers'))
    manage_exp_data = BooleanField(lazy_gettext('Can manage experiment data'))
    view_exp_data = BooleanField(lazy_gettext('Can view experiment data'))
    manage_formats = BooleanField(lazy_gettext('Can create formats'))
    generate_reports = BooleanField(lazy_gettext('Can generate reports'))


@module.route("/apps", methods=Common.http_methods)
@login_required
def apps():
    form = AppForm()

    apps_ = AppModel.load_all()

    if form.validate_on_submit():
        app = AppModel()
        app.title = form.title.data
        app.creator_id = current_user.uid
        app.key = uuid.uuid4().hex

        try:
            app.save()
        except ValueError as e:
            Common.flash(e, category="danger")
        else:
            return redirect(url_for("Admin.apps"))

    return render_template("admin/apps.html", apps=apps_, form=form, title=_("External apps"))


@module.route("/apps/delete/<uid>")
def delete_app(uid):
    AppModel.delete(uid)

    return redirect(url_for("Admin.apps"))


@module.route("/users")
def users():
    users_ = UserModel.load_all()

    return render_template("admin/users.html", users=users_, title=_("Users"))


@module.route("/create_user", defaults={"uid": None}, methods=Common.http_methods)
@module.route("/users/<uid>/edit", methods=Common.http_methods)
def user(uid):
    form = UserForm()

    if uid:
        user_ = UserModel.load(uid)

        if not user_:
            abort(404)

        form.username.default = user_.username
        form.email.default = user_.email

        for action in UserModel.action_shift:
            if user_.check_access(action):
                form[action].default = True

    else:
        user_ = UserModel()

    if form.validate_on_submit():
        mask = 0

        for action in UserModel.action_shift:
            if form[action].data:
                mask += 2 ** UserModel.action_shift[action]

        try:
            username = form.username.data

            password = None

            if form.password.data:
                if form.password.data != form.repeat_password.data:
                    raise ValueError(_("Passwords doesn't match"))

                password = generate_password_hash(form.password.data)
            else:
                if not uid:
                    raise ValueError(_("Password cannot be empty"))

            action_mask = mask
            email = form.email.data

            if uid:
                d = {
                    "email": email,
                    "username": username,
                    "action_mask": action_mask
                }

                if password:
                    d["password"] = password

                UserModel.update(cond={"_id": ObjectId(uid)}, upd=d)
            else:
                user_.email = email
                user_.username = username
                user_.password = password
                user_.action_mask = action_mask

                user_.save()
        except ValueError as e:
            Common.flash(e, category="danger")
        else:
            return redirect(url_for("Admin.users"))

    form.process()

    return render_template("admin/user.html", form=form, user=user, title=_("User"))


@module.route("/users/<uid>/delete")
def delete_user(uid):
    if uid != current_user.uid:
        UserModel.delete(uid)

    return redirect(url_for("Admin.users"))
