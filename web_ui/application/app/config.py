# -*- coding: utf-8 -*-


class AppConfig:
    SECRET_KEY = "031@2p[{<=:0+/K"
    DEBUG = True
    TESTING = True
    DB_HOST = "localhost"
    DB_PORT = 27017
    DB_USER = ""
    DB_PWD = ""
    DB_NAME = ""
    UPLOAD_FOLDER = '/tmp'
    PARSERS_OUTPUT_ROOT = '/tmp/parsers_output'
    PARSERS_OUTPUT_FOLDER_BATCHES = PARSERS_OUTPUT_ROOT + '/batches'
    PARSERS_OUTPUT_FOLDER_EXPERIMENTS = PARSERS_OUTPUT_ROOT + '/experiments'
    PARSERS_OUTPUT_FOLDER_SAMPLES = PARSERS_OUTPUT_ROOT + '/samples'
    PARSERS_WORKSPACES_FOLDER = '/tmp/parser_workspace'

