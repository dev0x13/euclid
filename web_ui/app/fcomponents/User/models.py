# -*- coding: utf-8 -*-

from application import db
from flask_login import current_user


class UserModel:

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.uid

    def __init__(self):
        super().__init__()
        self.username = ""
        self.email = ""
        self.password = ""

    @classmethod
    def load(cls, uid = None, login = None):
        pass

    def get_access_level(self, action):
        pass

