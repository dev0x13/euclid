from datetime import datetime
import json
import time

from flask import Blueprint, redirect, url_for, render_template, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField

from app.fcomponents import Common
from app.fcomponents.Formats.controllers import FormatModel
from app.fcomponents.Common import ModelFactory
from app.fcomponents.User.models import UserModel

module = Blueprint("Batches", __name__, url_prefix="/batches")


class BatchForm(FlaskForm):
    meta_ = HiddenField()
    format_uid = SelectField("Format: ", default=None)
    exp_format_uid = SelectField("Experiment format: ", default=None)


class BatchModel(ModelFactory.produce("batches",
                                      [
                                          "timestamp",
                                          "creator_uid",
                                          "parsers_uids",
                                          "meta",
                                          "format_uid",
                                          "exp_format_uid"
                                      ])):
    @classmethod
    def load_all(cls):
        inst = super().load_all()

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_id))
            i.timestamp = datetime.fromtimestamp(i.timestamp)

        return inst

    def save(self):
        Common.format_meta_eq(
            json.loads(FormatModel.load(self.format_uid).json_data),
            json.loads(self.meta)
        )

        super().save()


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
                batch.creator_id = current_user.uid
                batch.timestamp = time.time()
                batch.format_uid = form.format_uid.data
                batch.exp_format_uid = form.exp_format_uid.data

                try:
                    batch.save()
                except ValueError as e:
                    Common.flash(e, category="danger")
                else:
                    return redirect(url_for("Batches.index"))

    return render_template(
        "create_batch.html",
        form=form,
        formats=formats,
        title="Add batch"
    )


@module.route("/<uid>")
@login_required
def view(uid):
    # TODO: implement
    return redirect(url_for("Batches.index"))


@module.route("/<uid>/delete")
@login_required
def delete(uid):
    # batch = BatchModel.load(uid)
    #
    # TODO: Here come the checking if there are any experiments in the batch
    #

    BatchModel.delete(uid)

    return redirect(url_for("Batches.index"))
