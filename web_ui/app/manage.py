# -*- coding: utf-8 -*-

from flask_script import Manager, Server
from application import create_app
from application.config import AppConfig

app = create_app()
app.config.from_object(AppConfig)

manager = Manager(app)
manager.add_command("runserver", Server(host="127.0.0.1", port=5000))

if __name__ == '__main__':
    manager.run()

