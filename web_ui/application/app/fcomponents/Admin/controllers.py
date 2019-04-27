import uuid

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, validators
from app.fcomponents import Common
from app.fcomponents.Common import ModelFactory
from app.fcomponents.User.models import UserModel
from app import db

from werkzeug.security import generate_password_hash
from bson import ObjectId

module = Blueprint("Admin", __name__, url_prefix="/admin")


class AppModel(ModelFactory.produce("apps", ["key", "title", "creator_id"])):
    def save(self):
        if self.title == "":
            raise ValueError("Invalid title")

        super().save()

    @classmethod
    def load_all(cls):
        inst = super().load_all()

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_id))

        return inst


class FormatFormApp(FlaskForm):
    title = StringField([validators.DataRequired()], render_kw={"placeholder": "Title"})


class FormatFormUser(FlaskForm):
    title = StringField([validators.DataRequired()], render_kw={"placeholder": "Title"})
    password = StringField([validators.DataRequired()], render_kw={"placeholder": "Password"})
    isAdmin = BooleanField('Is admin')
    manageParsers = BooleanField('Can manage parsers')
    manageExprData = BooleanField('Can manage experiment data')
    viewExprData = BooleanField('Can view experiment data')
    createFormats = BooleanField('Can create formats')
    generateReports = BooleanField('Can generate reports')


@module.route("/apps", methods=Common.http_methods)
@login_required
def apps():
    form = FormatFormApp()

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

    return render_template("apps.html", apps=apps_, form=form, title="External apps")


@module.route("/apps/delete/<uid>")
def delete_app(uid):
    AppModel.delete(uid)

    return redirect(url_for("Admin.apps"))


@module.route("/usersTable", methods=Common.http_methods)
def users_table():
    users = db.users.find()

    create_form = FormatFormUser()
    set_form = FormatFormUser()

    if create_form.validate_on_submit():
        mask = 0
        for action in UserModel.action_shift:
            if create_form[action].data:
                mask += 2 ** UserModel.action_shift[action]

        try:
            db.users.insert_one({"username": create_form.title.data,
                                 "password": generate_password_hash(create_form.password.data),
                                 "action_mask": mask})
        except ValueError as e:
            Common.flash(e, category="danger")
        else:
            return redirect(url_for("Admin.users_table"))

    if set_form.validate_on_submit():
        mask = 0
        for action in UserModel.action_shift:
            if set_form[action].data:
                mask += 2 ** UserModel.action_shift[action]

        try:
            db.users.update_one({'_id': ObjectId(current_user.uid)}, {'$set': {"action_mask": mask}}, upsert=False)
        except ValueError as e:
            Common.flash(e, category="danger")
        else:
            return redirect(url_for("Admin.users_table"))

    return render_template("users.html", users=users, create_form=create_form, set_form=set_form, title="Users table")


@module.route("/usersTable/delete/<uid>")
def delete_user(uid):
    try:
        db.users.delete_one({"_id": ObjectId(uid)})
    except ValueError as e:
        Common.flash(e, category="danger")

    return redirect(url_for("Admin.users_table"))

