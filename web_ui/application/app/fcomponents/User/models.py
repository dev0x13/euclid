# -*- coding: utf-8 -*-

from app import db
from bson.objectid import ObjectId


class UserModel:

    # returns bit mask shift
    action_shift = {
        'isAdmin': 0,
        'manageParsers': 1,
        'manageExprData': 2,
		'viewExprData': 3,
		'createFormats': 4,
		'generateReports': 5
    }

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
        self.actionMask = int(31)

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
            user.actionMask = user_rec["actionMask"]
            user.uid = str(user_rec["_id"])
        else:
            return None

        return user

    @classmethod
    def get_name(cls, uid):
        rec = db.users.find_one({"_id": ObjectId(uid)})

        return rec["username"] if rec else None

    def get_access_level(self, action):
        if action in self.action_shift:  # TODO remove this "if", when actions are synchronized
            if (self.actionMask >> self.action_shift[action]) % 2 == 1:
                return True

        return False
