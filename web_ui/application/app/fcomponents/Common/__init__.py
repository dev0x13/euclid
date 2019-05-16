from functools import wraps

from flask import flash, redirect, abort
from app import db
from bson.objectid import ObjectId
from flask_login import current_user
from flask_babel import _

http_methods = ["GET", "POST"]


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
    def find_many(cls, cond):
        recs = db[cls.table].find(cond)

        return [cls.from_dict(rec) for rec in recs]

    @classmethod
    def load(cls, uid):
        return cls.find_one({"_id": ObjectId(uid)})

    @classmethod
    def load_all(cls):
        return cls.find_many({})

    @classmethod
    def delete(cls, uid):
        db[cls.table].remove({"_id": ObjectId(uid)})

    @classmethod
    def update(cls, cond, upd):
        db[cls.table].update(cond, {"$set": upd}, upsert=False)


class ModelFactory:
    @staticmethod
    def produce(table, fields):
        class Cls(Model):
            pass

        for f in fields:
            setattr(Cls, f, None)

        setattr(Cls, "table", table)

        return Cls


def format_meta_eq(format_, meta, key_path="ROOT"):
    for k in format_:
        if k not in meta:
            raise ValueError(_("Format doesn't match with metadata. Key missing: ") + "%s:%s" % (key_path, k))

        if isinstance(format_[k], dict):
            format_meta_eq(
                format_[k],
                meta[k],
                key_path + ":" + str(k)
            )
        else:
            if type(format_[k]) != type(meta[k]):
                raise ValueError(_("Format doesn't match with metadata. Invalid value type for key: ") + "%s:%s" % (key_path, k))


def check_access(action):
    def deco(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.check_access(action):
                return func(*args, **kwargs)
            else:
                abort(403)

        return wrapper

    return deco
