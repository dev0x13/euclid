from werkzeug.security import generate_password_hash
from pymongo import MongoClient

##########
# Params #
##########

db_host = "localhost"
db_port = 27017
default_username = "test"
default_password = "test"

##########

client = MongoClient(db_host, db_port)
db = client.euclid
inserted = db.users.insert_one({"username": default_username, "password": generate_password_hash(default_password)})
print(inserted.inserted_id)
