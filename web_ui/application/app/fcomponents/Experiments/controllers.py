import os
import zipfile
from datetime import datetime
import json
import time
from io import BytesIO

from bson import ObjectId
from flask import Blueprint, redirect, url_for, render_template, request, abort, send_from_directory, send_file
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext
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
    batch_uid = SelectField(lazy_gettext("Batch: "), default="0", coerce=str)
    format_uid = SelectField(lazy_gettext("Format: "), default="0", coerce=str)


class AttachParserForm(FlaskForm):
    parser_uid = SelectField(lazy_gettext("Parser: "), default=None, validators=[validators.DataRequired()])


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

    @classmethod
    def export(cls, uid, with_experiment=True):
        i = cls.load(uid)

        if not i:
            return None

        i = i.to_dict()

        i["creator_name"] = UserModel.get_name(i["creator_uid"])
        i["uid"] = uid

        if with_experiment:
            i["experiment_meta"] = ExpModel.export(i["experiment_uid"])

        del i["_id"]

        return i


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
                raise ValueError(_("Experiment is locked"))

            data_path = os.path.join(AppConfig.EXP_DATA_FOLDER, uid)
            if os.path.exists(data_path):
                shutil.rmtree(data_path)

            super().delete(uid)

    @classmethod
    def export(cls, uid, with_batch=True):
        i = cls.load(uid)

        if not i:
            return None

        i = i.to_dict()

        i["creator_name"] = UserModel.get_name(i["creator_uid"])
        i["uid"] = uid

        if i["batch_uid"] != "0" and with_batch:
            i["batch_meta"] = BatchModel.export(i["batch_uid"])

        i["timestamp"] = time.mktime(i["timestamp"].timetuple())
        i["format"] = FormatModel.export(i["format_uid"])
        i["meta"] = json.loads(i["meta"])

        samples = SampleModel.load_all_by_experiment(uid)

        i["samples"] = []
        for s in samples:
            i["samples"].append(SampleModel.export(s.uid, with_experiment=False))

        if "parsers_uids" in i:
            del i["parsers_uids"]

        del i["_id"]

        return i


@module.route("/")
@login_required
def index():
    experiments = ExpModel.load_all()

    return render_template("experiments/experiments.html", experiments=experiments, title=_("Experiments"))


@module.route("/create", methods=Common.http_methods)
@login_required
def create():
    form = ExpForm()

    formats = FormatModel.load_all()

    form.format_uid.choices = [("0", _("Nothing selected"))]
    form.format_uid.choices += [(a.uid, a.title) for a in formats]

    batches = BatchModel.load_all()

    form.batch_uid.choices = [("0", _("No batch"))]
    form.batch_uid.choices += [(a.uid, a.title) for a in batches]

    if form.validate_on_submit():
        if form.batch_uid.data == "0" and form.format_uid.data == "0":
            Common.flash(_("No format selected"), category="danger")
        else:
            meta_json = form.meta_.data

            try:
                json.loads(meta_json)
            except ValueError:
                Common.flash(_("Unable to parse JSON"), category="danger")
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
        title=_("Add experiment")
    )


def _process_exp_parsers(experiment, sample=None):
    from app.fcomponents.Parsers.controllers import ParserModel

    if not sample:
        parsers_output_dir = os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_EXPERIMENTS, experiment.uid)
    else:
        parsers_output_dir = os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_SAMPLES, sample.uid)

    experiment_parsers = []

    if experiment.parsers_uids:
        for p in experiment.parsers_uids:
            parser = ParserModel.load(p)
            parser_output = {}

            if experiment.locked:
                if sample:
                    error_code, msg = execute(parser, sample=sample)
                else:
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

    return experiment_parsers


@module.route("/<uid>", methods=Common.http_methods)
@login_required
def view(uid):
    from app.fcomponents.Parsers.controllers import ParserModel

    experiment = ExpModel.load(uid)

    if not experiment:
        abort(404)

    samples = SampleModel.load_all_by_experiment(uid)

    filepath = os.path.join(AppConfig.EXP_DATA_FOLDER, uid)

    form = AttachParserForm()

    form.parser_uid.choices = [(a.uid, a.title) for a in ParserModel.load_all()]

    experiment_parsers = _process_exp_parsers(experiment)

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
        title=_("Experiment")
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
def view_sample(sample_uid):
    sample = SampleModel.load(sample_uid)

    if not sample:
        abort(404)

    experiment = ExpModel.load(sample.experiment_uid)

    experiment_parsers = _process_exp_parsers(experiment, sample=sample)

    return render_template(
        "experiments/sample.html",
        experiment=experiment,
        experiment_parsers=experiment_parsers,
        sample=sample,
        title=_("Sample")
    )


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


@module.route('/samples/<sample_uid>/poutput/<img>', defaults={"exp_uid": None})
@module.route('/<exp_uid>/poutput/<img>', defaults={"sample_uid": None})
def parser_img_output(exp_uid, sample_uid, img):
    if exp_uid:
        return send_from_directory(os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_EXPERIMENTS, exp_uid), img,
                                   as_attachment=False)
    else:
        return send_from_directory(os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_SAMPLES, sample_uid), img,
                                   as_attachment=False)


@module.route('/samples/<sample_uid>/export', defaults={"exp_uid": None})
@module.route('/<exp_uid>/export', defaults={"sample_uid": None})
def export(exp_uid, sample_uid):
    archive = BytesIO()
    meta = {}
    data_path = ""
    archive_name = ""

    if exp_uid:
        meta = ExpModel.export(exp_uid)

        if not meta:
            abort(404)

        data_path = os.path.join(AppConfig.EXP_DATA_FOLDER, exp_uid)
        archive_name = "experiment_%s.zip" % exp_uid
    elif sample_uid:
        meta = SampleModel.export(sample_uid)
        sample = SampleModel.load(sample_uid)

        if not meta:
            abort(404)

        data_path = os.path.join(AppConfig.EXP_DATA_FOLDER, sample.experiment_uid, sample.file)
        archive_name = "sample_%s.zip" % sample_uid

    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as f:
        # If it's an experiment, then zip the whole directory
        if exp_uid:
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    f.write(os.path.join(root, file), file)
        elif sample_uid:
            # If it's just a sample, then zip a single file
            f.write(data_path, sample.file)

        f.writestr("meta.json", json.dumps(meta, sort_keys=True, indent=2))

    archive.seek(0)

    f.close()

    return send_file(archive,
                     attachment_filename=archive_name,
                     as_attachment=True)
