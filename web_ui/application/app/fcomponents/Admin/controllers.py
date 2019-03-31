import uuid

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, validators
from application.app.fcomponents import Helpers
from application.app.fcomponents.Helpers import ModelFactory
from application.app.fcomponents.User.models import UserModel

module = Blueprint("Admin", __name__, url_prefix ="/admin")


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


class FormatForm(FlaskForm):
    title = StringField([validators.DataRequired()], render_kw={"placeholder": "Title"})


@module.route("/apps", methods=Helpers.methods)
@login_required
def apps():
    form = FormatForm()

    apps_ = AppModel.load_all()

    if form.validate_on_submit():
        app = AppModel()
        app.title = form.title.data
        app.creator_id = current_user.uid
        app.key = uuid.uuid4().hex

        try:
            app.save()
        except ValueError as e:
            Helpers.flash(e, category="danger")
        else:
            return redirect(url_for("Admin.apps"))

    return render_template("apps.html", apps=apps_, form=form, title="External apps")


@module.route("/apps/delete/<uid>")
@login_required
def delete_app(uid):
    AppModel.delete(uid)

    return redirect(url_for("Admin.apps"))
