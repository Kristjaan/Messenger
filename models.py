import os
from sqla_wrapper import SQLAlchemy

db = SQLAlchemy(
    os.getenv("DATABASE_URL", "sqlite:///localhost.sqlite")
)  # this connects to a database either on Heroku or on localhost


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    #secret = db.Column(db.Integer)
    session_token = db.Column(db.String)
    text_sent = db.Column(db.String)
    text_received = db.Column(db.String)

