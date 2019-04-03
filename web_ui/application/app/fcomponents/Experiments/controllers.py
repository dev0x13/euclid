from datetime import datetime
import json
import time

from flask import Blueprint, redirect, url_for, render_template, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField

from app.fcomponents import Common
from app.fcomponents.Formats.controllers import FormatModel
from app.fcomponents.Batches.controllers import BatchModel
from app.fcomponents.User.models import UserModel

module = Blueprint("Experiments", __name__, url_prefix="/experiments")


class ExpForm(FlaskForm):
    meta_ = HiddenField()
    batch_uid = SelectField("Batch: ", default=None)
    format_uid = SelectField("Format: ", default=None)


class ExpModel(Common.ModelFactory.produce("experiments",
                                      [
                                          "timestamp",
                                          "creator_uid",
                                          "parsers_uids",
                                          "meta",
                                          "format_uid",
                                          "batch_uid"
                                          "locked"
                                      ])):
    @classmethod
    def load_all(cls):
        inst = super().load_all()

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_id))
            i.timestamp = datetime.fromtimestamp(i.timestamp)

        return inst

    @classmethod
    def load_all_by_batch(cls, batch_uid):
        inst = super().find_many({"batch_uid": batch_uid})

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
    experiments = ExpModel.load_all()

    return render_template("experiments/experiments.html", experiments=experiments, title="Experiments")


@module.route("/create", methods=Common.http_methods)
@login_required
def create():
    form = ExpForm()

    formats = FormatModel.load_all()

    form.format_uid.choices = [(0, "Nothing selected")]
    form.format_uid.choices += [(a.uid, a.title) for a in formats]

    batches = BatchModel.load_all()

    form.batch_uid.choices = [(0, "No batch")]
    form.batch_uid.choices += [(a.uid, a.title) for a in batches]

    if form.validate_on_submit():
        if form.format_uid == 0:
            Common.flash("No format selected", category="danger")
        else:
            meta_json = form.meta_.data

            try:
                json.loads(meta_json)
            except ValueError:
                Common.flash("Unable to parse JSON", category="danger")
            else:
                exp = ExpModel()
                exp.meta = meta_json
                exp.creator_uid = current_user.uid
                exp.batch_uid = current_user.uid
                exp.timestamp = time.time()
                exp.format_uid = form.format_uid.data

                try:
                    exp.save()
                except ValueError as e:
                    Common.flash(e, category="danger")
                else:
                    if exp.batch_uid == 0:
                        return redirect(url_for("Experiments.index"))
                    else:
                        return redirect(url_for("Batches.view", uid=exp.batch_uid))

    return render_template(
        "experiments/create_experiment.html",
        form=form,
        formats=formats,
        title="Add experiment"
    )


@module.route("/<uid>")
@login_required
def view(uid):
    # TODO: implement
    return redirect(url_for("Experiments.index"))


@module.route("/<uid>/lock")
@login_required
def lock(uid):
    ExpModel.lock(uid)

    return redirect(url_for("Experiments.view", uid=uid))


@module.route("/<uid>/delete")
@login_required
def delete(uid):
    # TODO: Here come the checking if experiments is locked

    ExpModel.delete(uid)

    return redirect(url_for("Experiments.index"))
