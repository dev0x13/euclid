import os
import docker
from docker.errors import ContainerError

from app.bcomponents.parser_backend.executor import PARSER_BASE, parser_tmp_workspace


def validate_parser(code):
    with parser_tmp_workspace() as tmp_workspace_path:
        docker_volumes = {}

        docker_volumes[tmp_workspace_path] = {
            "bind": "/env/workspace",
            "mode": "ro"
        }

        with open(os.path.join(tmp_workspace_path, "parser.py"), "w") as c:
            c.write(PARSER_BASE)
            c.write(code)

        docker_client = docker.from_env()

        try:
            docker_client.containers.run("euclid-parser-env", "python validator.py", volumes=docker_volumes)
        except ContainerError as e:
            return 1, str(e)

        return 0, _("All OK!")
