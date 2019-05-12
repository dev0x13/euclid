import shutil
import os
import uuid
from contextlib import contextmanager

import docker
import pickle

from app.config import AppConfig

from docker.errors import ContainerError

PARSER_BASE = '''
import os

class Parser:
    def __init__(self):
        self.text_buffer = ""
        self.image_buffer = []

    def print_text(self, text):
        self.text_buffer += text

    def print_image(self, image, format="png"):
        self.image_buffer.append({"image": image, "format": format})
        
    @staticmethod
    def load(exp_uid, filename, mode="binary"):
        read_mode = "rb" if mode == "binary" else "r"
        
        data = None
        
        with open(os.path.join("input", exp_uid, filename), read_mode) as f:
            data = f.read()
            
        return data
     \n\n'''


@contextmanager
def parser_tmp_workspace(*args, **kwds):
    tmp_workspace_uid = str(uuid.uuid4())
    tmp_workspace_path = os.path.join(AppConfig.PARSERS_WORKSPACES_FOLDER, tmp_workspace_uid)

    os.mkdir(tmp_workspace_path)

    try:
        yield tmp_workspace_path
    finally:
        shutil.rmtree(tmp_workspace_path)


def execute(parser, batch=None, experiment=None, sample=None, clear_output=False, custom_output_dir=None):
    from app.fcomponents.Experiments.controllers import ExpModel, SampleModel

    if not AppConfig.PARSERS_ENGINE_ENABLED:
        return 1, "Parsers engine disabled by config"

    with parser_tmp_workspace() as tmp_workspace_path:
        open(os.path.join(tmp_workspace_path, "__init__.py"), 'a').close()

        with open(os.path.join(tmp_workspace_path, "parser.py"), "w") as f:
            f.write("PARSER_UID = \"%s\"\n\n" % parser.uid)
            f.write(PARSER_BASE)
            f.write(parser.code)

        if batch:
            data = {
                "meta": batch.meta,
                "uid": batch.uid,
                "experiments": []
            }

            for exp in ExpModel.load_all_by_batch(batch.uid):
                samples = [s.file for s in SampleModel.load_all_by_experiment(exp.uid)]

                data["experiments"].append(
                    {"meta": exp.meta, "samples": samples}
                )

            with open(os.path.join(tmp_workspace_path, "batch.pkl"), "wb") as f:
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        elif experiment:
            data = {
                "meta": experiment.meta,
                "uid": experiment.uid,
                "samples": [{"file": s.file, "uid": s.uid} for s in SampleModel.load_all_by_experiment(experiment.uid)]
            }

            with open(os.path.join(tmp_workspace_path, "experiment.pkl"), "wb") as f:
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
        elif sample:
            data = {"file": sample.file, "uid": sample.uid}

            with open(os.path.join(tmp_workspace_path, "sample.pkl"), "wb") as f:
                pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)

        docker_client = docker.from_env()

        docker_volumes = {}

        docker_volumes[tmp_workspace_path] = {
            "bind": "/env/workspace",
            "mode": "ro"
        }

        output_dir = ""

        if batch:
            output_path = os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_BATCHES, batch.uid, "%s.txt" % parser.uid)

            if os.path.exists(output_path):
                return 0, ""

            for exp in ExpModel.load_all_by_batch(batch.uid):
                docker_volumes[os.path.join(AppConfig.EXP_DATA_FOLDER, exp.uid)] = {
                    "bind": "/env/input/%s" % exp.uid,
                    "mode": "ro"
                }

            output_dir = os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_BATCHES, batch.uid)

        elif experiment:
            output_path = os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_EXPERIMENTS, experiment.uid, "%s.txt" % parser.uid)

            if os.path.exists(output_path):
                return 0, ""

            docker_volumes[os.path.join(AppConfig.EXP_DATA_FOLDER, experiment.uid)] = {
                "bind": "/env/input/%s" % experiment.uid,
                "mode": "ro"
            }

            output_dir = os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_EXPERIMENTS, experiment.uid)

        elif sample:
            output_path = os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_SAMPLES, sample.uid, "%s.txt" % parser.uid)

            if os.path.exists(output_path):
                return 0, ""

            docker_volumes[os.path.join(AppConfig.EXP_DATA_FOLDER, sample.experiment_uid, sample.file)] = {
                "bind": "/env/input/%s" % sample.file,
                "mode": "ro"
            }

            output_dir = os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_SAMPLES, sample.uid)

        if custom_output_dir:
            output_dir = custom_output_dir

        docker_volumes[output_dir] = {
            "bind": "/env/output",
            "mode": "rw"
        }

        try:
            docker_client.containers.run(
                "euclid-parser-env",
                "python executor.py %s" % ("clear_output" if clear_output else ""),
                volumes=docker_volumes
            )
        except ContainerError as e:
            return 1, str(e)

        return 0, "All OK!"
