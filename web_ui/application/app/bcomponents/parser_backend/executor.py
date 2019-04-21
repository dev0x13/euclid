import json
import os
import uuid
import docker

from app.config import AppConfig

from app.fcomponents.Experiments.controllers import ExpModel
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


def execute(parser, batch=None, experiment=None, sample=None):
    tmp_workspace_uid = str(uuid.uuid4())
    tmp_workspace_path = os.path.join(AppConfig.PARSERS_WORKSPACES_FOLDER, tmp_workspace_uid)

    if not os.path.exists(tmp_workspace_path):
        os.mkdir(tmp_workspace_path)

    open(os.path.join(tmp_workspace_path, "__init__.py"), 'a').close()

    with open(os.path.join(tmp_workspace_path, "parser.py"), "w") as f:
        f.write("PARSER_UID = \"%s\"\n\n" % parser.uid)
        f.write(PARSER_BASE)
        f.write(parser.code)

    if batch:
        with open(os.path.join(tmp_workspace_path, "batch.json"), "w") as f:
            f.write(json.dumps(batch))
    elif experiment:
        with open(os.path.join(tmp_workspace_path, "experiment.json"), "w") as f:
            f.write(json.dumps(experiment))
    elif sample:
        with open(os.path.join(tmp_workspace_path, "sample.json"), "w") as f:
            f.write(json.dumps(sample))

    docker_client = docker.from_env()

    docker_volumes = {}

    if batch:
        for exp in ExpModel.load_all_by_batch(batch.uid):
            docker_volumes[os.path.join(AppConfig.UPLOAD_FOLDER, exp.uid)] = {
                "bind": "/env/input/%s" % exp.uid,
                "mode": "ro"
            }
        docker_volumes[os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_BATCHES, batch.uid)] = {
            "bind": "/env/output",
            "mode": "rw"
        }
    elif experiment:
        docker_volumes[os.path.join(AppConfig.UPLOAD_FOLDER, experiment.uid)] = {
            "bind": "/env/input/%s" % experiment.uid,
            "mode": "ro"
        }
        docker_volumes[os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_EXPERIMENTS, experiment.uid)] = {
            "bind": "/env/output",
            "mode": "rw"
        }
    elif sample:
        docker_volumes[os.path.join(AppConfig.UPLOAD_FOLDER, sample.experiment_uid, sample.file)] = {
            "bind": "/env/input/%s/%s" % (sample.experiment_uid, sample.file),
            "mode": "ro"
        }
        docker_volumes[os.path.join(AppConfig.PARSERS_OUTPUT_FOLDER_SAMPLES, sample.uid)] = {
            "bind": "/env/output",
            "mode": "rw"
        }

    try:
        output = docker_client.containers.run("euclid_parser_env", volumes=docker_volumes)
    except ContainerError:
        pass
