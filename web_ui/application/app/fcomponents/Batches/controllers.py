from datetime import datetime
import json
import time

from flask import Blueprint, redirect, url_for, render_template, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField

from application.app.fcomponents import Helpers
from application.app.fcomponents.Formats.controllers import FormatModel
from application.app.fcomponents.Helpers import ModelFactory
from application.app.fcomponents.User.models import UserModel

module = Blueprint("Batches", __name__, url_prefix ="/batches")


class BatchForm(FlaskForm):
    meta_ = HiddenField()
    format_uid = SelectField("Format: ", default=None)


class BatchModel(ModelFactory.produce("batches",
                                      [
                                          "timestamp",
                                          "creator_id",
                                          "parsers_ids",
                                          "meta",
                                          "format_uid"
                                      ])):
    @classmethod
    def load_all(cls):
        inst = super().load_all()

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_id))
            i.timestamp = datetime.fromtimestamp(i.timestamp)

        return inst

    def save(self):
        _ = json.loads(self.meta)

        for k in json.loads(FormatModel.load(self.format_uid).json_data):
            if k not in _:
                raise ValueError("Format doesn't match with metadata. Key missing: %s" % k)

        super().save()


@module.route("/")
@login_required
def index():
    batches = BatchModel.load_all()

    return render_template("batches.html", batches=batches, title="Batches")


@module.route("/create", methods=Helpers.methods)
@login_required
def create():
    form = BatchForm()

    formats = FormatModel.load_all()

    form.format_uid.choices = [(0, "Nothing selected")]
    form.format_uid.choices += [(a.uid, a.title) for a in formats]

    if form.validate_on_submit():
        if form.format_uid == 0:
            Helpers.flash("No format selected", category="danger")
        else:
            meta_json = form.meta_.data

            try:
                json.loads(meta_json)
            except ValueError:
                Helpers.flash("Unable to parse JSON", category="danger")
            else:
                batch = BatchModel()
                batch.meta = meta_json
                batch.creator_id = current_user.uid
                batch.timestamp = time.time()
                batch.format_uid = form.format_uid.data

                try:
                    batch.save()
                except ValueError as e:
                    Helpers.flash(e, category="danger")
                else:
                    return redirect(url_for("Batches.index"))

    return render_template(
        "create_batch.html",
        form=form,
        formats=formats,
        title="Add batch"
    )


@module.route("/delete/<uid>")
@login_required
def delete(uid):
    # batch = BatchModel.load(uid)
    #
    # TODO: Here come the checking if there are any experiments in the batch
    #

    BatchModel.delete(uid)

    return redirect(url_for("Batches.index"))
