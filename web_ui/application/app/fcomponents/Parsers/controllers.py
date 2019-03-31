from datetime import datetime
import json
import time

from flask import Blueprint, redirect, url_for, render_template, request
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField

from app.fcomponents import Helpers
from app.fcomponents.Formats.controllers import FormatModel
from app.fcomponents.Helpers import ModelFactory
from app.fcomponents.User.models import UserModel

module = Blueprint("Parsers", __name__, url_prefix="/parsers")


class ParserForm(FlaskForm):
    code = HiddenField()


class ParserModel(ModelFactory.produce("parsers",
                                      [
                                          "title",
                                          "creator_id",
                                      ])):
    @classmethod
    def load_all(cls):
        inst = super().load_all()

        for i in inst:
            setattr(i, "creator_name", UserModel.get_name(i.creator_id))

        return inst

    def save(self):
        # TODO: verification logic

        super().save()


@module.route("/")
@login_required
def index():
    parsers = ParserModel.load_all()

    return render_template("parsers.html", parsers=parsers, title="Parsers")


@module.route("/create", methods=Helpers.methods)
@login_required
def create():
    form = ParserForm()

    if form.validate_on_submit():
        pass

    return render_template(
        "parser.html",
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
