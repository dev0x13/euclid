import os
import sys
import inspect
import uuid

from flask import Blueprint, redirect, url_for, render_template, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, validators, StringField

from app.fcomponents import Common
from app.fcomponents.Formats.controllers import FormatModel
from app.fcomponents.Common import ModelFactory
from app.fcomponents.User.models import UserModel
from app.bcomponents.parser_backend.executor import PARSER_BASE

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


# This is a draft for parsers validation.
# Note: wacked fo now, will be done inside Docker container

sys.path.append("/tmp/")

from contextlib import contextmanager


@contextmanager
def parser_tmp_module(*args, **kwds):
    tmp_module_uid = kwds["tmp_module_uid"]
    try:
        yield tmp_module_uid
    finally:
        os.remove("/tmp/%s.py" % tmp_module_uid)


def validate_parser(code):
    code = PARSER_BASE + code

    tmp_module_uid = "tmp_%s" % uuid.uuid4().hex

    with open("/tmp/%s.py" % tmp_module_uid, "w") as c:
        c.write(code)

    with parser_tmp_module(tmp_module_uid=tmp_module_uid):
        try:
            _module = __import__(tmp_module_uid, fromlist=["Parser", "ParserImpl"])
            ParserImpl = _module.ParserImpl
            Parser = _module.Parser
        except ImportError:
            return 1, "`ParserImpl` class is not found"
        except Exception as e:
            return 1, str(e)

        if not issubclass(ParserImpl, Parser):
            return 1, "`ParserImpl` class should inherit `Parser`"

        p = getattr(ParserImpl, "process_sample", None)
        if not callable(p):
            return 1, "missing `process_sample` method"
        else:
            if "sample" not in inspect.getfullargspec(p)[0]:
                return 1, "`process_sample` method missing `sample` argument"

        p = getattr(ParserImpl, "process_experiment", None)
        if not callable(p):
            return 1, "missing `process_experiment` method"
        else:
            if "experiment" not in inspect.getfullargspec(p)[0]:
                return 1, "`process_experiment` method missing `experiment` argument"

        p = getattr(ParserImpl, "process_batch", None)
        if not callable(p):
            return 1, "missing `process_batch` method"
        else:
            if "batch" not in inspect.getfullargspec(p)[0]:
                return 1, "`process_batch` method missing `batch` argument"

        return 0, "All OK!"


@module.route("/")
@login_required
def index():
    parsers = ParserModel.load_all()

    return render_template("parsers/parsers.html", parsers=parsers, title="Parsers")


@module.route("/validate", methods=Common.http_methods)
@login_required
def validate():
    if "code" in request.form:
        return jsonify(validate_parser(request.form["code"]))

    return {}


@module.route("/create", methods=Common.http_methods)
@login_required
def create():
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


    return render_template(
        "parsers/parser.html",
        form=form,
        title="Create parser"
    )


@module.route("/delete/<uid>")
@login_required
def delete(uid):
    # parser = ParserModel.load(uid)
    #
    # TODO: Here come the checking if there are any experiments, batches or samples
    # using this parser
    #

    ParserModel.delete(uid)

    return redirect(url_for("Parsers.index"))


@module.route("/view/<uid>")
@login_required
def view(uid):
    # TODO: implement

    return redirect(url_for("Parsers.index"))


@module.route("/docs")
@login_required
def docs():
    return render_template("parsers/docs.html")

