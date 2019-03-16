from flask import flash

methods = ["GET", "POST"]


def flash_message(message, class_="danger"):
    if message:
        flash(message, class_)
