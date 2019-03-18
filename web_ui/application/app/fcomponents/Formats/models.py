# -*- coding: utf-8 -*-

from app import db
from bson.objectid import ObjectId


class FormatModel:
    def __init__(self):
        self.uid = ""
        self.title = ""
        self.json_data = ""

    def to_dict(self):
        json_ = {"json_data": self.json_data, "title": self.title}

        return json_

    @classmethod
    def from_dict(cls, dict_):
        format_ = cls()

        format_.uid = str(dict_["_id"])
        format_.json_data = dict_["json_data"]
        format_.title = dict_["title"]

        return format_

    def save(self):
        conflicts = db.formats.find_one({"title": self.title})

        if conflicts:
            raise ValueError("Format with specified title already exists")

        db.formats.insert_one(self.to_dict())

    @classmethod
    def load(cls, uid):
        format_rec = db.formats.find_one({"_id": ObjectId(uid)})

        if format_rec:
            format_ = cls()

            format_.json_data = format_rec["username"]
            format_.title = format_rec["title"]
            format_.uid = str(format_rec["_id"])

            return format_
        else:
            return None

    @staticmethod
    def load_all():
        format_recs = db.formats.find({})

        formats = []

        for f in format_recs:
            formats.append(FormatModel.from_dict(f))

        return formats

    @staticmethod
    def delete(uid):
        db.formats.remove({"_id": ObjectId(uid)})
