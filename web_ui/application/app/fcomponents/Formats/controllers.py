from flask import Blueprint, redirect, url_for, render_template, request
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, validators
import json
import app.fcomponents.Helpers as Helpers
from app.fcomponents.Formats.models import FormatModel

module = Blueprint("Formats", __name__, url_prefix="/formats")


class FormatForm(FlaskForm):
    format = HiddenField()
    title = StringField([validators.DataRequired()], render_kw={"placeholder": "Title"})


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
    FormatModel.delete(uid)

    return redirect(url_for("Formats.index"))


