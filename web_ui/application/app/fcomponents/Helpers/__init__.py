from flask import flash
from application.app import db
from bson.objectid import ObjectId


methods = ["GET", "POST"]


def flash_message(message, class_="danger"):
    if message:
        flash(message, class_)


class Model:
    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

    def __init__(self):
        self.uid = ""

    def to_dict(self):
        json_ = {}

        for f in self:
            if f[0] != "uid":
                json_[f[0]] = f[1]

        return json_

    @classmethod
    def from_dict(cls, dict_):
        instance = cls()

        instance.uid = str(dict_["_id"])

        for k, v in dict_.items():
            setattr(instance, k, v)

        return instance

    def save(self):
        db[self.table].insert_one(self.to_dict())

    @classmethod
    def find_one(cls, cond):
        rec = db[cls.table].find_one(cond)

        return cls.from_dict(rec) if rec else None

    @classmethod
    def load(cls, uid):
        return cls.find_one({"_id": ObjectId(uid)})

    @classmethod
    def load_all(cls):
        recs = db[cls.table].find({})

        instances = []

        for f in recs:
            instances.append(cls.from_dict(f))

        return instances

    @classmethod
    def delete(cls, uid):
        db[cls.table].remove({"_id": ObjectId(uid)})


class ModelFactory:
    @staticmethod
    def produce(table, fields):
        class Cls(Model):
            pass

        for f in fields:
            setattr(Cls, f, None)

        setattr(Cls, "table", table)

        return Cls





