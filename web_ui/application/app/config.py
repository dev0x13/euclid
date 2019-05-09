# -*- coding: utf-8 -*-


class AppConfigLinux:
    SECRET_KEY = "031@2p[{<=:0+/K"
    DEBUG = True
    TESTING = True

    DB_HOST = "localhost"
    DB_PORT = 27017
    DB_USER = ""
    DB_PWD = ""
    DB_NAME = ""

    DATA_ROOT_FOLDER = '/tmp/euclid'
    EXP_DATA_FOLDER = DATA_ROOT_FOLDER + "/exp_data"
    PARSERS_WORKSPACES_FOLDER = DATA_ROOT_FOLDER + '/parser_workspace'
    PARSERS_OUTPUT_ROOT_FOLDER = DATA_ROOT_FOLDER + '/parsers_output'
    PARSERS_OUTPUT_FOLDER_BATCHES = PARSERS_OUTPUT_ROOT_FOLDER + '/batches'
    PARSERS_OUTPUT_FOLDER_EXPERIMENTS = PARSERS_OUTPUT_ROOT_FOLDER + '/experiments'
    PARSERS_OUTPUT_FOLDER_SAMPLES = PARSERS_OUTPUT_ROOT_FOLDER + '/samples'

    PARSERS_ENGINE_ENABLED = True


class AppConfigWindows:
    SECRET_KEY = "031@2p[{<=:0+/K"
    DEBUG = True
    TESTING = True

    DB_HOST = "localhost"
    DB_PORT = 27017
    DB_USER = ""
    DB_PWD = ""
    DB_NAME = ""

    DATA_ROOT_FOLDER = 'C:\\tmp\\euclid'
    EXP_DATA_FOLDER = DATA_ROOT_FOLDER + "\\exp_data"
    PARSERS_WORKSPACES_FOLDER = DATA_ROOT_FOLDER + '\\parser_workspace'
    PARSERS_OUTPUT_ROOT_FOLDER = DATA_ROOT_FOLDER + '\\parsers_output'
    PARSERS_OUTPUT_FOLDER_BATCHES = PARSERS_OUTPUT_ROOT_FOLDER + '\\batches'
    PARSERS_OUTPUT_FOLDER_EXPERIMENTS = PARSERS_OUTPUT_ROOT_FOLDER + '\\experiments'
    PARSERS_OUTPUT_FOLDER_SAMPLES = PARSERS_OUTPUT_ROOT_FOLDER + '\\samples'

    PARSERS_ENGINE_ENABLED = False


# Change this line is you are using Linux
AppConfig = AppConfigLinux
