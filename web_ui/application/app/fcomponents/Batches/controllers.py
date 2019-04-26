import os
from datetime import datetime
import json
import time

from bson import ObjectId
from flask import Blueprint, redirect, url_for, render_template, request, send_from_directory
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, validators

from app.fcomponents import Common
from app.fcomponents.Formats.controllers import FormatModel
from app.fcomponents.Common import ModelFactory
from app.fcomponents.User.models import UserModel

from app.bcomponents.parser_backend.executor import execute

from app.config import AppConfig

module = Blueprint("Batches", __name__, url_prefix="/batches")


class BatchForm(FlaskForm):
    meta_ = HiddenField()
    format_uid = SelectField("Format: ", default=None, validators=[validators.DataRequired()])
    title = StringField("Title: ", validators=[validators.DataRequired()])
    exp_format_uid = SelectField("Experiment format: ", default=None, validators=[validators.DataRequired()])


class AttachParserForm(FlaskForm):
    parser_uid = SelectField("Parser: ", default=None, validators=[validators.DataRequired()])


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
                batch.parsers_uid = []
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


@module.route("/<uid>", methods=Common.http_methods)
@login_required
def view(uid):
    from app.fcomponents.Experiments.controllers import ExpModel
    from app.fcomponents.Parsers.controllers import ParserModel

    batch = BatchModel.load(uid)
    experiments = ExpModel.load_all_by_batch(uid)

    form = AttachParserForm()

    batch_parsers = []

    parsers_output_dir = os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_BATCHES, uid)

    if batch.parsers_uids:
        for p in batch.parsers_uids:
            execute(ParserModel.load(p), batch=batch)

            parser_output = {}

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

            batch_parsers.append({
                "parser": ParserModel.load(p),
                "output": parser_output
            })

    form.parser_uid.choices = [(a.uid, a.title) for a in ParserModel.load_all()]

    if form.validate_on_submit():
        if not batch.parsers_uids:
            batch.parsers_uids = []

        new_parser_uid = form.parser_uid.data

        if new_parser_uid not in batch.parsers_uids:
            BatchModel.update(
                {"_id": ObjectId(uid)},
                {"parsers_uids": batch.parsers_uids + [form.parser_uid.data]}
            )

        return redirect(url_for("Batches.view", uid=uid))

    return render_template(
        "batches/batch.html",
        form=form,
        batch=batch,
        batch_parsers=batch_parsers,
        experiments=experiments,
        title="Batch"
    )


@module.route("/<batch_uid>/remove_parser/<parser_uid>", methods=Common.http_methods)
@login_required
def remove_parser(batch_uid, parser_uid):
    batch = BatchModel.load(batch_uid)

    if parser_uid in batch.parsers_uids:
        batch.parsers_uids.remove(parser_uid)

        BatchModel.update(
            {"_id": ObjectId(batch_uid)},
            {"parsers_uids": batch.parsers_uids}
        )

    return redirect(url_for("Batches.view", uid=batch_uid))


@module.route("/<uid>/delete")
@login_required
def delete(uid):
    try:
        BatchModel.delete(uid)
    except ValueError as e:
        Common.flash(str(e), category="danger")

    return redirect(url_for("Batches.index"))


@module.route('/<batch_uid>/poutput/<img>')
def parser_img_output(batch_uid, img):
    return send_from_directory(os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_BATCHES, batch_uid), img, as_attachment=False)
