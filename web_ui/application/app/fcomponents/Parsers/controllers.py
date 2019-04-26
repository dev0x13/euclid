import os
import sys
import inspect
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

        batches = BatchModel.load_all()

        for b in batches:
            if b.parsers_uids:
                if uid in b.parsers_uids:
                    raise ValueError("Some batches use this parser")

        super().delete(uid)


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
        "parsers/create_parser.html",
        form=form,
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

