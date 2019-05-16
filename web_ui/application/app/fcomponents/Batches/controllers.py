import os
import zipfile
from datetime import datetime
import json
import time
from io import BytesIO

from bson import ObjectId
from flask import Blueprint, redirect, url_for, render_template, request, send_from_directory, abort, send_file
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext
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
    format_uid = SelectField(lazy_gettext("Format: "), default=None, validators=[validators.DataRequired()])
    title = StringField(lazy_gettext("Title: "), validators=[validators.DataRequired()])
    exp_format_uid = SelectField(lazy_gettext("Experiment format: "), default=None, validators=[validators.DataRequired()])


class AttachParserForm(FlaskForm):
    parser_uid = SelectField(lazy_gettext("Parser: "), default=None, validators=[validators.DataRequired()])


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
            raise ValueError(_("Batch is locked"))

        super().delete(uid)

    @classmethod
    def export(cls, uid, with_experiments=False):
        from app.fcomponents.Experiments.controllers import ExpModel

        i = cls.load(uid)

        if not i:
            return None

        i = i.to_dict()

        i["creator_name"] = UserModel.get_name(i["creator_uid"])
        i["uid"] = uid

        i["timestamp"] = time.mktime(i["timestamp"].timetuple())
        i["format"] = FormatModel.export(i["format_uid"])

        if with_experiments:
            experiments = ExpModel.load_all_by_batch(uid)
            i["experiments"] = []

            for e in experiments:
                i["experiments"].append(ExpModel.export(e.uid, with_batch=False))

        i["meta"] = json.loads(i["meta"])

        if "parsers_uids" in i:
            del i["parsers_uids"]

        del i["_id"]

        return i


@module.route("/")
@login_required
def index():
    batches = BatchModel.load_all()

    return render_template("batches/batches.html", batches=batches, title=_("Batches"))


@module.route("/create", methods=Common.http_methods)
@login_required
def create():
    form = BatchForm()

    formats = FormatModel.load_all()

    form.format_uid.choices = [(0, _("Nothing selected"))]
    form.format_uid.choices += [(a.uid, a.title) for a in formats]

    form.exp_format_uid.choices = form.format_uid.choices

    if form.validate_on_submit():
        if form.format_uid == 0 or form.exp_format_uid == 0:
            Common.flash(_("No format selected"), category="danger")
        else:
            meta_json = form.meta_.data

            try:
                json.loads(meta_json)
            except ValueError:
                Common.flash(_("Unable to parse JSON"), category="danger")
            else:
                batch = BatchModel()
                batch.meta = meta_json
                batch.title = form.title.data
                batch.creator_uid = current_user.uid
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
        title=_("Add batch")
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
            parser = ParserModel.load(p)
            parser_output = {}

            if batch.locked:
                error_code, msg = execute(parser, batch=batch)

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

            batch_parsers.append({
                "parser": parser,
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
        title=_("Batch")
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


@module.route('/<batch_uid>/export')
def export(batch_uid):
    from app.fcomponents.Experiments.controllers import ExpModel

    archive = BytesIO()

    meta = BatchModel.export(batch_uid, with_experiments=True)
    experiments = ExpModel.load_all_by_batch(batch_uid)

    if not meta:
        abort(404)

    archive_name = "batch_%s.zip" % batch_uid

    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as f:
        for e in experiments:
            data_path = os.path.join(AppConfig.EXP_DATA_FOLDER, e.uid)

            for root, dirs, files in os.walk(data_path):
                for file in files:
                    f.write(os.path.join(root, file), os.path.join(e.uid, file))

        f.writestr("meta.json", json.dumps(meta, sort_keys=True, indent=2))

    archive.seek(0)

    f.close()

    return send_file(archive,
                     attachment_filename=archive_name,
                     as_attachment=True)
