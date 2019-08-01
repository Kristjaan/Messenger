import hashlib
import json
import os
import requests
from flask import Flask, url_for, redirect, render_template, request, make_response, Response, Request
import datetime
import random
import uuid
from models import db, User

try:
    import secrets  # only needed for localhost, that's why it's in the try/except statement
except Exception as e:
    pass

app = Flask(__name__)

db.create_all()  # create new tables in the database


@app.route("/")
def index():
    query = "Vienna,AT"
    unit = "metric"  # use "imperial" for Fahrenheit
    api_key = os.environ.get('API_KEY')

    url_current = f"https://api.openweathermap.org/data/2.5/weather?q={query}&units={unit}&appid={api_key}"
    data = requests.get(url=url_current)  # GET request to the OpenWeatherMap API

    return render_template("index.html", data=data.json())


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        email = request.form.get("email")
        password = hashlib.sha256(request.form.get("password").encode("utf-8")).hexdigest()

        user = db.query(User).filter_by(email=email).first()

        if not user:
            user = User(password=password, email=email)
            db.add(user)
            db.commit()

        if password == user.password:
            # create a random session token for this user
            session_cookie = str(uuid.uuid4())

            # save the session token in a database
            user.session_token = session_cookie
            db.add(user)
            db.commit()

            response: Response = make_response(redirect(url_for('messenger', session_cookie=session_cookie)))
            # render template --> show html now on this url where you are; redirect move to new ur, make get request
            # there
            response.set_cookie("session_cookie", session_cookie, httponly=True, samesite='Strict')

            return response
        return redirect(url_for('login'))


texts = []
messages = {}

# TODO: Add delete, edit, list all users, details?, change password, profile page; Who's logged in...
@app.route("/messenger/<session_cookie>", methods=["GET", "POST"])
def messenger(session_cookie):
    if request.method == "GET":
        user = db.query(User).filter_by(session_token=session_cookie).first()
        return render_template("messenger.html", session_cookie=user.session_token, email=user.email)

    elif request.method == "POST":
        user1 = db.query(User).filter_by(session_token=session_cookie).first()
        email = request.form.get("email")
        user2 = db.query(User).filter_by(email=email).first()
        text = request.form.get("text")
        if user2:
            text_received = f"From {user1.email}: {text}"
            if user2.text_received:
                text_received = user2.text_received + "|" + text_received
                user2.text_received = text_received
                db.add(user2)
                db.commit()
            else:
                user2.text_received = text_received
                db.add(user2)
                db.commit()

        if user1.text_sent:
            text_sent = f"To {email}: {text}"
            text_sent = user1.text_sent + "|" + text_sent
            user1.text_sent = text_sent
            db.add(user1)
            db.commit()
        else:
            user1.text_sent = f"To {email}: {text}"
            db.add(user1)
            db.commit()

        return render_template("sent.html", text=user1.text_sent, session_cookie=user1.session_token, email=user1.email)


@app.route("/messenger/<session_cookie>/sent")
def sent(session_cookie):
    user = db.query(User).filter_by(session_token=session_cookie).first()
    return render_template("sent.html", session_cookie=user.session_token, text=user.text_sent, email=user.email)


@app.route("/messenger/<session_cookie>/received")
def received(session_cookie):
    user = db.query(User).filter_by(session_token=session_cookie).first()
    return render_template("received.html", session_cookie=user.session_token, text=user.text_received, email=user.email)


@app.route("/messenger/<session_cookie>/sent/delete", methods=["GET"])
def sent_delete(session_cookie):
    user = db.query(User).filter_by(session_token=session_cookie).first()
    user.text_sent = None
    db.commit()
    return redirect(url_for("sent", session_cookie=user.session_token))


@app.route("/messenger/<session_cookie>/received/delete", methods=["GET"])
def received_delete(session_cookie):
    user = db.query(User).filter_by(session_token=session_cookie).first()
    user.text_received = None
    db.commit()
    return redirect(url_for("received", session_cookie=user.session_token))


@app.route("/about-me")
def about():
    return render_template("about.html")


if __name__ == '__main__':
    app.run(debug=True)
