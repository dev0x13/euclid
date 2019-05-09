import base64
import os
import shutil
import uuid

from flask import Blueprint, redirect, url_for, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, validators, StringField

from app.fcomponents import Common
from app.fcomponents.Formats.controllers import FormatModel
from app.fcomponents.Common import ModelFactory
from app.fcomponents.User.models import UserModel
from app.bcomponents.parser_backend.executor import PARSER_BASE
from app.bcomponents.parser_backend.validator import validate_parser
from app.bcomponents.parser_backend.executor import execute

from app.config import AppConfig

module = Blueprint("Parsers", __name__, url_prefix="/parsers")


class ParserForm(FlaskForm):
    code = HiddenField()
    title = StringField("Title: ", validators=[validators.DataRequired()], render_kw={"placeholder": "Title"})


class ParserModel(ModelFactory.produce("parsers",
                                      [
                                          "title",
                                          "creator_id",
                                          "code"
                                      ])):
    @classmethod
    def load_all(cls):
        inst = super().load_all()

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_id))

        return inst

    def save(self):
        res = validate_parser(self.code)

        if res[0] != 0:
            raise ValueError(res[1])

        super().save()

    @classmethod
    def delete(cls, uid):
        from app.fcomponents.Batches.controllers import BatchModel
        from app.fcomponents.Experiments.controllers import ExpModel

        for b in BatchModel.load_all():
            if b.parsers_uids:
                if uid in b.parsers_uids:
                    raise ValueError("Some batches use this parser")

        for e in ExpModel.load_all():
            if e.parsers_uids:
                if uid in e.parsers_uids:
                    raise ValueError("Some experiments use this parser")

        super().delete(uid)


@module.route("/")
@login_required
def index():
    parsers = ParserModel.load_all()

    return render_template("parsers/parsers.html", parsers=parsers, title="Parsers")


@module.route("/validate", methods=Common.http_methods)
@login_required
def validate():
    from app.fcomponents.Experiments.controllers import SampleModel, ExpModel
    from app.fcomponents.Batches.controllers import BatchModel

    static_validation_res = ()
    runtime_validation_res = ()
    runtime_output = {}

    if "code" in request.form:
        # Static validation

        static_validation_res = validate_parser(request.form["code"])

        # Runtime validation

        if "debug_input_type" in request.form and "debug_input_uid" in request.form:
            tmp_parser = ParserModel()
            tmp_parser.code = request.form["code"]
            tmp_parser.uid = str(uuid.uuid4())

            tmp_output_dir = os.path.join(AppConfig.PARSERS_OUTPUT_ROOT_FOLDER, "tmp_%s" % tmp_parser.uid)

            os.mkdir(tmp_output_dir)

            input_type = request.form["debug_input_type"]
            input_uid = request.form["debug_input_uid"]

            if input_type == "sample":
                sample = SampleModel.load(input_uid)

                if sample:
                    runtime_validation_res = execute(tmp_parser, sample=sample, custom_output_dir=tmp_output_dir)
                else:
                    runtime_validation_res = (1, "Input not found")
            elif input_type == "experiment":
                experiment = ExpModel.load(input_uid)

                if experiment:
                    runtime_validation_res = execute(tmp_parser, experiment=experiment, custom_output_dir=tmp_output_dir)
                else:
                    runtime_validation_res = (1, "Input not found")
            elif input_type == "batch":
                batch = BatchModel.load(input_uid)

                if batch:
                    runtime_validation_res = execute(tmp_parser, batch=batch, custom_output_dir=tmp_output_dir)
                else:
                    runtime_validation_res = (1, "Input not found")
            elif input_type == "none":
                pass
            else:
                runtime_validation_res = (1, "Invalid input type")

            if runtime_validation_res and runtime_validation_res[0] == 0:
                parser_txt = os.path.join(tmp_output_dir, "%s.txt" % tmp_parser.uid)

                if os.path.exists(parser_txt):
                    with open(parser_txt, "r") as txt:
                        runtime_output["text"] = txt.read()

                runtime_output["img"] = []
                i = 0

                while True:
                    img = "%s_img_%i.png" % (tmp_parser.uid, i)
                    parser_img = os.path.join(tmp_output_dir, img)

                    if os.path.exists(parser_img):
                        with open(parser_img, "rb") as f:
                            runtime_output["img"].append(str(base64.b64encode(f.read()), "utf-8"))
                        i += 1
                    else:
                        break

            shutil.rmtree(tmp_output_dir)

    return jsonify({
        "static": static_validation_res,
        "runtime": runtime_validation_res,
        "runtime_output": runtime_output
    })


@module.route("/create", methods=Common.http_methods)
@login_required
def create():
    from app.fcomponents.Experiments.controllers import SampleModel, ExpModel
    from app.fcomponents.Batches.controllers import BatchModel

    form = ParserForm()

    if form.validate_on_submit():
        code, msg = validate_parser(form.code.data)

        if code != 0:
            Common.flash("Validation error: " + msg, category="danger")
        else:
            parser = ParserModel()
            parser.title = form.title.data
            parser.code = form.code.data
            parser.creator_uid = current_user.uid

            parser.save()

            return redirect(url_for("Parsers.index"))

    # For debug input
    samples_uids = [s.uid for s in SampleModel.load_all()]
    experiments_uids = [e.uid for e in ExpModel.load_all()]
    batches_uids = [b.uid for b in BatchModel.load_all()]

    return render_template(
        "parsers/create_parser.html",
        form=form,
        samples_uids=samples_uids,
        experiments_uids=experiments_uids,
        batches_uids=batches_uids,
        title="Create parser"
    )


@module.route("/delete/<uid>")
@login_required
def delete(uid):
    try:
        ParserModel.delete(uid)
    except ValueError as e:
        Common.flash(str(e), category="danger")

    return redirect(url_for("Parsers.index"))


@module.route("/view/<uid>")
@login_required
def view(uid):
    parser = ParserModel.load(uid)

    if not parser:
        abort(404)

    return render_template(
        "parsers/parser.html",
        parser=parser,
        title="Parser"
    )


@module.route("/docs")
@login_required
def docs():
    return render_template("parsers/docs.html")

