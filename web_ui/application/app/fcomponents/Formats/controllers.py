from flask import Blueprint, redirect, url_for, render_template, request
from flask_login import login_required
from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext
from wtforms import HiddenField, StringField, validators
import json
import app.fcomponents.Common as Common
from app import db
from app.fcomponents.Common import ModelFactory

module = Blueprint("Formats", __name__, url_prefix="/formats")


class FormatForm(FlaskForm):
    format = HiddenField()
    title = StringField([validators.DataRequired()], render_kw={"placeholder": lazy_gettext("Title")})


class FormatModel(ModelFactory.produce("formats", ["json_data", "title"])):
    def save(self):
        if self.title == "":
            raise ValueError(_("Invalid title"))

        conflicts = db[self.table].find_one({"title": self.title})

        if conflicts:
            raise ValueError(_("Format with specified title already exists"))

        super().save()

    @classmethod
    def delete(cls, uid):
        from app.fcomponents.Batches.controllers import BatchModel
        from app.fcomponents.Experiments.controllers import ExpModel

        batch = BatchModel.find_one({"format_uid": uid})
        if batch:
            raise ValueError(_("The format is used by following batch:") + "<b>%s</b>" % batch.title)

        if ExpModel.find_one({"format_uid": uid}):
            raise ValueError(_("The format is used by some experiments"))

        super().save()

    @classmethod
    def export(cls, uid):
        i = cls.load(uid)

        if not i:
            return None

        i = i.to_dict()

        i["uid"] = uid
        i["json_data"] = json.loads(i["json_data"])

        del i["_id"]

        return i

@module.route("/")
@login_required
def index():
    formats = FormatModel.load_all()

    return render_template("formats/formats.html", formats=formats, title=_("Formats"))


@module.route("/create", methods=Common.http_methods)
@login_required
def create():
    form = FormatForm()

    if form.validate_on_submit():
        format_json = form.format.data

        try:
            json.loads(format_json)
        except ValueError:
            Common.flash(_("Unable to parse JSON"), category="danger")
        else:
            format_ = FormatModel()
            format_.json_data = format_json
            format_.title = form.title.data

            try:
                format_.save()
            except ValueError as e:
                Common.flash(e, category="danger")
            else:
                return redirect(url_for("Formats.index"))

    return render_template("formats/create_format.html", form=form, title=_("Add format"))


@module.route("/delete/<uid>", methods=Common.http_methods)
@login_required
def delete(uid):
    # TODO: check access

    try:
        FormatModel.delete(uid)
    except ValueError as e:
        Common.flash(str(e), category="danger")

    return redirect(url_for("Formats.index"))


