# -*- coding: utf-8 -*-

from app import db
from bson.objectid import ObjectId
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
        self.uid = ""
        self.username = ""
        self.email = ""
        self.password = ""

    @classmethod
    def load(cls, uid=None, username=None):
        if uid is not None:
            user_rec = db.users.find_one({"_id": ObjectId(uid)})
        elif username is not None:
            user_rec = db.users.find_one({"username": username})
        else:
            return None

        user = UserModel()

        if user_rec:
            user.username = user_rec["username"]
            user.password = user_rec["password"]
            user.uid = str(user_rec["_id"])
        else:
            return None

        return user

    def get_access_level(self, action):
        return True
