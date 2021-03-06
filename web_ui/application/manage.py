# -*- coding: utf-8 -*-

from flask_script import Manager, Server
from app import create_app
from app.config import AppConfig

app = create_app()
app.config.from_object(AppConfig)

manager = Manager(app)
manager.add_command("runserver", Server(host=AppConfig.HOST, port=5000))

if __name__ == '__main__':
    manager.run()

