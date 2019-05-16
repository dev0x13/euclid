# -*- coding: utf-8 -*-

from bson.objectid import ObjectId

from flask_babel import _

from app.fcomponents.Common import ModelFactory


class UserModel(ModelFactory.produce("users", ["username", "email", "password", "action_mask", "locale"])):
    # returns bit mask shift
    action_shift = {
        'is_admin': 0,
        'manage_parsers': 1,
        'manage_exp_data': 2,
        'view_exp_data': 3,
        'manage_formats': 4,
        'generate_reports': 5
    }

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.uid

    def save(self):
        if not self.action_mask:
            self.action_mask = int(63)

        if not self.locale:
            self.locale = "ru"

        if self.username == "" or self.password == "":
            raise ValueError(_("Invalid username or password"))

        test = UserModel.load(username=self.username)

        if test:
            if test.uid != self.uid:
                raise ValueError(_("Non unique username"))

        # TODO: implement action mask validation

        super().save()

    @classmethod
    def load(cls, uid=None, username=None):
        if uid is not None:
            user = cls.find_one({"_id": ObjectId(uid)})

            if user:
                if not user.locale:
                    user.locale = "ru"
        elif username is not None:
            user = cls.find_one ({"username": username})

            if user:
                if not user.locale:
                    user.locale = "ru"
        else:
            return None

        return user

    @classmethod
    def get_name(cls, uid):
        rec = cls.load(uid=uid)

        return rec.username if rec else None

    def change_locale(self, locale):
        if locale not in ("ru", "en"):
            return

        self.locale = locale
        self.update(
            {"_id": ObjectId(self.uid)},
            {"locale": locale}
        )

    def check_access(self, action):
        if action in self.action_shift:  # TODO remove this "if", when actions are synchronized
            if (self.action_mask >> self.action_shift[action]) % 2 == 1:
                return True

        return False
