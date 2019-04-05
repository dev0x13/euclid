import os
from datetime import datetime
import json
import time

from bson import ObjectId
from flask import Blueprint, redirect, url_for, render_template, request, abort, send_from_directory
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import HiddenField, SelectField, validators

from app.fcomponents import Common
from app.fcomponents.Formats.controllers import FormatModel
from app.fcomponents.Batches.controllers import BatchModel
from app.fcomponents.User.models import UserModel

from app.config import AppConfig

module = Blueprint("Experiments", __name__, url_prefix="/experiments")


class ExpForm(FlaskForm):
    meta_ = HiddenField()
    batch_uid = SelectField("Batch: ", default="0", coerce=str)
    format_uid = SelectField("Format: ", default="0", coerce=str)


class SampleModel(Common.ModelFactory.produce("samples",
                                      [
                                          "creator_uid",
                                          "experiment_uid"
                                          "file"
                                      ])):
    @classmethod
    def load_all_by_experiment(cls, experiment_uid):
        inst = super().find_many({"experiment_uid": experiment_uid})

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_uid))

        return inst


class ExpModel(Common.ModelFactory.produce("experiments",
                                      [
                                          "timestamp",
                                          "creator_uid",
                                          "parsers_uids",
                                          "meta",
                                          "format_uid",
                                          "batch_uid"
                                          "locked",
                                          "num_samples"
                                      ])):
    @classmethod
    def load_all(cls):
        inst = super().load_all()

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_uid))
            if i.batch_uid != "0":
                batch = BatchModel.load(i.batch_uid)
                setattr(i, "batch_title", batch.title if batch else None)
            i.timestamp = datetime.fromtimestamp(i.timestamp)

        return inst

    @classmethod
    def load(cls, uid):
        i = super().load(uid)

        setattr(i, "creator_name", UserModel.get_name(i.creator_uid))
        if i.batch_uid != "0":
            batch = BatchModel.load(i.batch_uid)
            setattr(i, "batch_title", batch.title if batch else None)
        i.timestamp = datetime.fromtimestamp(i.timestamp)

        return i

    @classmethod
    def load_all_by_batch(cls, batch_uid):
        inst = super().find_many({"batch_uid": batch_uid})

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_uid))
            i.timestamp = datetime.fromtimestamp(i.timestamp)

        return inst

    def save(self):
        Common.format_meta_eq(
            json.loads(FormatModel.load(self.format_uid).json_data),
            json.loads(self.meta)
        )

        super().save()

    @classmethod
    def lock(cls, uid):
        samples = SampleModel.load_all_by_experiment(uid)

        cls.update({"_id": ObjectId(uid)}, {"locked": True, "num_samples": samples.count()})

    @classmethod
    def delete(cls, uid):
        exp = cls.load(uid)

        if exp:
            if exp.locked:
                raise ValueError("Experiment is locked")

            os.rmdir(os.path.join(AppConfig.UPLOAD_FOLDER, uid))

            super().delete(uid)


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

    form.format_uid.choices = [("0", "Nothing selected")]
    form.format_uid.choices += [(a.uid, a.title) for a in formats]

    batches = BatchModel.load_all()

    form.batch_uid.choices = [("0", "No batch")]
    form.batch_uid.choices += [(a.uid, a.title) for a in batches]

    if form.validate_on_submit():
        if form.batch_uid.data == "0" and form.format_uid.data == "0":
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
                exp.batch_uid = form.batch_uid.data
                exp.timestamp = time.time()
                exp.format_uid = form.format_uid.data if exp.batch_uid == "0" else BatchModel.load(exp.batch_uid).format_uid

                try:
                    exp.save()
                except ValueError as e:
                    Common.flash(e, category="danger")
                else:
                    if exp.batch_uid == "0":
                        return redirect(url_for("Experiments.index"))
                    else:
                        return redirect(url_for("Batches.view", uid=exp.batch_uid))
    for field, errors in form.errors.items():
        for error in errors:
            Common.flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'error')
    return render_template(
        "experiments/create_experiment.html",
        form=form,
        formats=formats,
        batches=batches,
        title="Add experiment"
    )


@module.route("/<uid>", methods=Common.http_methods)
@login_required
def view(uid):
    experiment = ExpModel.load(uid)

    if not experiment:
        abort(404)

    samples = SampleModel.load_all_by_experiment(uid)

    filepath = os.path.join(AppConfig.UPLOAD_FOLDER, uid)

    if "samples[]" in request.files:
        files = request.files.getlist('samples[]', None)

        if files:
            for file in files:
                filename = secure_filename(file.filename)

                if not os.path.exists(filepath):
                    os.makedirs(filepath)

                file.save(os.path.join(filepath, filename))

                sample = SampleModel()
                sample.file = filename
                sample.creator_uid = current_user.uid
                sample.experiment_uid = uid

                sample.save()

    # TODO: parser logic

    return render_template("experiments/experiment.html", experiment=experiment, samples=samples, title="Experiment")


@module.route("/<uid>/lock")
@login_required
def lock(uid):
    ExpModel.lock(uid)

    return redirect(url_for("Experiments.view", uid=uid))


@module.route("/<uid>/delete")
@login_required
def delete(uid):
    try:
        ExpModel.delete(uid)
    except ValueError as e:
        Common.flash(e, category="danger")

    return redirect(url_for("Experiments.index"))


@module.route("/download_sample/<sample_uid>")
@login_required
def download_sample(sample_uid):
    sample = SampleModel.load(sample_uid)

    if not sample:
        abort(404)

    return send_from_directory(
        os.path.join(AppConfig.UPLOAD_FOLDER,
                     sample.experiment_uid),
        sample.file, as_attachment=True)

