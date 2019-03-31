from flask import Blueprint, redirect, url_for, render_template, request
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, validators
import json
import app.fcomponents.Helpers as Helpers
from app import db
from app.fcomponents.Helpers import ModelFactory

module = Blueprint("Formats", __name__, url_prefix="/formats")


class FormatForm(FlaskForm):
    format = HiddenField()
    title = StringField([validators.DataRequired()], render_kw={"placeholder": "Title"})


class FormatModel(ModelFactory.produce("formats", ["json_data", "title"])):
    def save(self):
        if self.title == "":
            raise ValueError("Invalid title")

        conflicts = db[self.table].find_one({"title": self.title})

        if conflicts:
            raise ValueError("Format with specified title already exists")

        super().save()

    @classmethod
    def delete(cls, uid):
        from app.fcomponents.Batches.controllers import BatchModel

        batch = BatchModel.find_one({"format_uid": uid})
        if batch:
            raise ValueError("The format is used by following batch: <b>%s</b>" % batch.uid)

        # TODO: Here come the same logic for experiments and samples:
        # if BatchModel.find_one({"format_uid": uid}):
        #    raise ValueError("This format is used by some experiments")
        #
        # if BatchModel.find_one({"format_uid": uid}):
        #    raise ValueError("This format is used by some samples")

        super().save()


@module.route("/")
@login_required
def index():
    formats = FormatModel.load_all()

    return render_template("formats.html", formats=formats, title="Formats")


@module.route("/create", methods=Helpers.methods)
@login_required
def create():
    form = FormatForm()

    if form.validate_on_submit():
        format_json = form.format.data

        try:
            json.loads(format_json)
        except ValueError:
            Helpers.flash("Unable to parse JSON", category="danger")
        else:
            format_ = FormatModel()
            format_.json_data = format_json
            format_.title = form.title.data

            try:
                format_.save()
            except ValueError as e:
                Helpers.flash(e, category="danger")
            else:
                return redirect(url_for("Formats.index"))

    return render_template("create_format.html", form=form, title="Add format")


@module.route("/delete/<uid>", methods=Helpers.methods)
@login_required
def delete(uid):
    # TODO: check access

    try:
        FormatModel.delete(uid)
    except ValueError as e:
        Helpers.flash(str(e), category="danger")

    return redirect(url_for("Formats.index"))


