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
import shutil

from app.fcomponents import Common
from app.fcomponents.Formats.controllers import FormatModel
from app.fcomponents.Batches.controllers import BatchModel
from app.fcomponents.User.models import UserModel

from app.config import AppConfig

from app.bcomponents.parser_backend.executor import execute

module = Blueprint("Experiments", __name__, url_prefix="/experiments")


class ExpForm(FlaskForm):
    meta_ = HiddenField()
    batch_uid = SelectField("Batch: ", default="0", coerce=str)
    format_uid = SelectField("Format: ", default="0", coerce=str)

class AttachParserForm(FlaskForm):
    parser_uid = SelectField("Parser: ", default=None, validators=[validators.DataRequired()])


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
                                          "meta",
                                          "format_uid",
                                          "parsers_uids",
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

        cls.update({"_id": ObjectId(uid)}, {"locked": True, "num_samples": len(samples)})

    @classmethod
    def delete(cls, uid):
        exp = cls.load(uid)

        if exp:
            if exp.locked:
                raise ValueError("Experiment is locked")

            data_path = os.path.join(AppConfig.EXP_DATA_FOLDER, uid)
            if os.path.exists(data_path):
                shutil.rmtree(data_path)

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
                exp.locked = False
                exp.meta = meta_json
                exp.creator_uid = current_user.uid
                exp.batch_uid = form.batch_uid.data
                exp.timestamp = time.time()
                exp.num_samples = 0
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
    else:
        batch_uid = request.args.get("batch_uid")
        batch = BatchModel.load(batch_uid) if batch_uid else None

        if batch_uid and batch:
            form.batch_uid.default = batch_uid
            form.process()

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
    from app.fcomponents.Parsers.controllers import ParserModel

    experiment = ExpModel.load(uid)

    if not experiment:
        abort(404)

    samples = SampleModel.load_all_by_experiment(uid)

    filepath = os.path.join(AppConfig.EXP_DATA_FOLDER, uid)

    parsers_output_dir = os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_EXPERIMENTS, uid)

    form = AttachParserForm()

    form.parser_uid.choices = [(a.uid, a.title) for a in ParserModel.load_all()]

    if form.validate_on_submit():
        if not experiment.parsers_uids:
            experiment.parsers_uids = []

        new_parser_uid = form.parser_uid.data

        if new_parser_uid not in experiment.parsers_uids:
            ExpModel.update(
                {"_id": ObjectId(uid)},
                {"parsers_uids": experiment.parsers_uids + [form.parser_uid.data]}
            )

        return redirect(url_for("Experiments.view", uid=uid))

    experiment_parsers = []

    if experiment.parsers_uids:
        for p in experiment.parsers_uids:
            parser = ParserModel.load(p)
            parser_output = {}

            if experiment.locked:
                error_code, msg = execute(parser, experiment=experiment)

                if error_code != 0:
                    Common.flash("Parser `%s` error: %s" % (parser.title, msg))

                parser_txt = os.path.join(parsers_output_dir, "%s.txt" % p)

                if os.path.exists(parser_txt):
                    with open(parser_txt, "r") as txt:
                        parser_output["text"] = txt.read()

                parser_output["img"] = []
                i = 0

                while True:
                    img = "%s_img_%i.png" % (p, i)
                    parser_img = os.path.join(parsers_output_dir, img)

                    if os.path.exists(parser_img):
                        parser_output["img"].append(img)
                        i += 1
                    else:
                        break

            experiment_parsers.append({
                "parser": parser,
                "output": parser_output
            })

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

        return redirect(url_for("Experiments.view", uid=uid))

    return render_template(
        "experiments/experiment.html",
        experiment=experiment,
        experiment_parsers=experiment_parsers,
        samples=samples,
        form=form,
        title="Experiment"
    )


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
        Common.flash(str(e), category="danger")

    return redirect(url_for("Experiments.index"))


@module.route("/samples/<sample_uid>")
@login_required
def view_samples(sample_uid):
    sample = SampleModel.load(sample_uid)

    if not sample:
        abort(404)

    # TODO: implement

    return redirect(url_for("Experiments.index"))


@module.route("/download_sample/<sample_uid>")
@login_required
def download_sample(sample_uid):
    sample = SampleModel.load(sample_uid)

    if not sample:
        abort(404)

    return send_from_directory(
        os.path.join(AppConfig.EXP_DATA_FOLDER,
                     sample.experiment_uid),
        sample.file, as_attachment=True)


@module.route("/<experiment_uid>/remove_parser/<parser_uid>", methods=Common.http_methods)
@login_required
def remove_parser(experiment_uid, parser_uid):
    exp = ExpModel.load(experiment_uid)

    if parser_uid in exp.parsers_uids:
        exp.parsers_uids.remove(parser_uid)

        ExpModel.update(
            {"_id": ObjectId(experiment_uid)},
            {"parsers_uids": exp.parsers_uids}
        )

    return redirect(url_for("Experiments.view", uid=experiment_uid))


@module.route('/<exp_uid>/poutput/<img>')
def parser_img_output(exp_uid, img):
    return send_from_directory(os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_EXPERIMENTS, exp_uid), img, as_attachment=False)
