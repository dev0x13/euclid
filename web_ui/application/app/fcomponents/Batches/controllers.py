from datetime import datetime
import json
import time

from bson import ObjectId
from flask import Blueprint, redirect, url_for, render_template, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, validators

from app.fcomponents import Common
from app.fcomponents.Formats.controllers import FormatModel
from app.fcomponents.Common import ModelFactory
from app.fcomponents.User.models import UserModel

module = Blueprint("Batches", __name__, url_prefix="/batches")


class BatchForm(FlaskForm):
    meta_ = HiddenField()
    format_uid = SelectField("Format: ", default=None, validators=[validators.DataRequired()])
    title = StringField("Title: ", validators=[validators.DataRequired()])
    exp_format_uid = SelectField("Experiment format: ", default=None, validators=[validators.DataRequired()])


class BatchModel(ModelFactory.produce("batches",
                                      [
                                          "timestamp",
                                          "creator_uid",
                                          "parsers_uids",
                                          "meta",
                                          "title",
                                          "format_uid",
                                          "exp_format_uid",
                                          "locked"
                                      ])):
    @classmethod
    def load_all(cls):
        from app.fcomponents.Experiments.controllers import ExpModel

        inst = super().load_all()

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_uid))
            setattr(i, "num_experiments", len(ExpModel.load_all_by_batch(i.uid)))
            i.timestamp = datetime.fromtimestamp(i.timestamp)

        return inst

    @classmethod
    def load(cls, uid):
        i = super().load(uid)

        setattr(i, "creator_name", UserModel.get_name(i.creator_uid))
        i.timestamp = datetime.fromtimestamp(i.timestamp)

        return i

    def save(self):
        Common.format_meta_eq(
            json.loads(FormatModel.load(self.format_uid).json_data),
            json.loads(self.meta)
        )

        super().save()

    @classmethod
    def delete(cls, uid):
        from application.app.fcomponents.Experiments.controllers import ExpModel

        experiments = ExpModel.load_all_by_batch(uid)

        if len(experiments) != 0:
            raise ValueError("Batch is locked")

        super().delete(uid)


@module.route("/")
@login_required
def index():
    batches = BatchModel.load_all()

    return render_template("batches/batches.html", batches=batches, title="Batches")


@module.route("/create", methods=Common.http_methods)
@login_required
def create():
    form = BatchForm()

    formats = FormatModel.load_all()

    form.format_uid.choices = [(0, "Nothing selected")]
    form.format_uid.choices += [(a.uid, a.title) for a in formats]

    form.exp_format_uid.choices = form.format_uid.choices

    if form.validate_on_submit():
        if form.format_uid == 0 or form.exp_format_uid == 0:
            Common.flash("No format selected", category="danger")
        else:
            meta_json = form.meta_.data

            try:
                json.loads(meta_json)
            except ValueError:
                Common.flash("Unable to parse JSON", category="danger")
            else:
                batch = BatchModel()
                batch.meta = meta_json
                batch.title = form.title.data
                batch.creator_id = current_user.uid
                batch.timestamp = time.time()
                batch.format_uid = form.format_uid.data
                batch.exp_format_uid = form.exp_format_uid.data
                batch.locked = False

                try:
                    batch.save()
                except ValueError as e:
                    Common.flash(e, category="danger")
                else:
                    return redirect(url_for("Batches.index"))

    return render_template(
        "batches/create_batch.html",
        form=form,
        formats=formats,
        title="Add batch"
    )


@module.route("/<uid>")
@login_required
def view(uid):
    from app.fcomponents.Experiments.controllers import ExpModel

    batch = BatchModel.load(uid)
    experiments = ExpModel.load_all_by_batch(uid)

    return render_template("batches/batch.html", batch=batch, experiments=experiments, title="Batch")


@module.route("/<uid>/delete")
@login_required
def delete(uid):
    try:
        BatchModel.delete(uid)
    except ValueError as e:
        Common.flash(str(e), category="danger")

    return redirect(url_for("Batches.index"))
