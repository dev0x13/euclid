# -*- coding: utf-8 -*-

from flask import Flask, request, redirect, url_for, render_template
from flask_login import LoginManager, current_user
from flask_bootstrap import Bootstrap
from pymongo import MongoClient
from app.config import AppConfig

client = MongoClient(AppConfig.DB_HOST, AppConfig.DB_PORT)
db = client.euclid

from app.fcomponents.User.models import UserModel


def create_app():
    app = Flask(__name__)

    Bootstrap(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "/"

    @login_manager.user_loader
    def user_loader(uid):
        return UserModel.load(uid)

    import app.fcomponents.Admin.controllers as AdminModule
    import app.fcomponents.Batches.controllers as BatchesModule
    import app.fcomponents.Experiments.controllers as ExperimentsModule
    import app.fcomponents.Samples.controllers as SamplesModule
    import app.fcomponents.Parsers.controllers as ParsersModule
    import app.fcomponents.Tools.controllers as ToolsModule
    import app.fcomponents.User.controllers as UsersModule
    import app.fcomponents.Formats.controllers as FormatsModule

    app.register_blueprint(AdminModule.module)
    app.register_blueprint(BatchesModule.module)
    app.register_blueprint(ExperimentsModule.module)
    app.register_blueprint(SamplesModule.module)
    app.register_blueprint(ParsersModule.module)
    app.register_blueprint(ToolsModule.module)
    app.register_blueprint(UsersModule.module)
    app.register_blueprint(FormatsModule.module)

    @app.before_request
    def check_valid_login():
        if request.endpoint and 'login' not in request.endpoint and 'static' not in request.endpoint\
                and not current_user.is_authenticated:
            return redirect(url_for("User.login", next=request.endpoint))

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(exception):
        app.logger.error(exception)
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def access_denied_error(exception):
        return render_template('errors/403.html'), 403

    @app.route('/')
    def index():
        return render_template("index.html")

    return app

