from flask import Blueprint, redirect, url_for, render_template
from flask_login import login_required

module = Blueprint("Formats", __name__, url_prefix="/formats")


@module.route("/")
@login_required
def index():
    return render_template("formats.html", title="Formats")


@module.route("/create")
@login_required
def create():
    return render_template("create_format.html", title="Add format")
