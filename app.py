import os

import imghdr
import pandas as pd
import numpy as np
import sqlite3
import urllib.request
import urllib.parse
from twilio.rest import Client
from random import randint
from uuid import uuid4
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_file, send_from_directory
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import login_required

pd.set_option("display.max_rows", None, "display.max_columns", None)
UPLOAD_PATH = "uploads"

os.environ["TWILIO_ACCOUNT_SID"] = ""
os.environ["TWILIO_AUTH_TOKEN"] = ""
os.environ["FROM_NUMBER"] = ""

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_PATH"] = UPLOAD_PATH
app.config["MAX_CONTENT_LENGTH"] = 10240 * 10240
app.config["UPLOAD_EXTENSIONS"] = [".jpg", ".png", ".jpeg"]
Session(app)

conn = sqlite3.connect("plumber.db")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        with sqlite3.connect("plumber.db") as conn:
            if session["type"] == "PLUMBER":
                invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.dealer_id = users.id WHERE plumber_id ='{}' AND redeemed = 'False'""".format(int(session["user_id"])))
                gifts = conn.execute("""SELECT gift, date FROM redemption WHERE plumber_id = {} AND gift_status != 'Fasle'""".format(session["user_id"]))
                points = conn.execute("""SELECT SUM(invoices.points) FROM invoices WHERE plumber_id = {}""".format(session["user_id"]))
                inv = len(list(invoices))
                gif = len(list(gifts))
                if inv != 0 and gif != 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.dealer_id = users.id WHERE plumber_id ='{}'""".format(int(session["user_id"])))
                    gifts = conn.execute("""SELECT gift, date FROM redemption WHERE plumber_id = {} and gift_status != 'Fasle'""".format(session["user_id"]))
                    return render_template("index.html", invoices=invoices, gifts=gifts, points=points)
                elif inv == 0 and gif != 0:
                    gifts = conn.execute("""SELECT gift, date FROM redemption WHERE plumber_id = {} and gift_status != 'Fasle'""".format(session["user_id"]))
                    notif = "No pending invoices. Please contact your store."
                    return render_template("index.html", notif=notif, gifts=gifts, points=points)
                elif inv != 0 and gif == 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.dealer_id = users.id WHERE plumber_id ='{}'""".format(int(session["user_id"])))
                    notif = "No gifts issued yet. Please contact your store."
                    return render_template("index.html", notif=notif, invoices=invoices, gifts=gifts, points=points)
                elif inv == 0 and gif == 0:
                    notif = "No pending invoices or gifts issued. Please contact your store."
                    return render_template("index.html", notif=notif, invoices=invoices, gifts=gifts, points=points)

            elif session["type"] == "TRADER":
                invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.dealer_id ='{}' AND invoices.redeemed='False'""".format(int(session["user_id"])))
                gifts = conn.execute("""SELECT redemption.gift, redemption.date, users.first_name, users.last_name FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.dealer_id = {} AND redemption.gift_status != 'Fasle'""".format(session["user_id"]))
                points = conn.execute("""SELECT users.first_name, users.last_name, SUM(invoices.points), invoices.plumber_id, users.redeem_request FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_approved = 'True' AND invoices.dealer_id = '{}' GROUP BY invoices.plumber_id""".format(session["user_id"]))
                inv = len(list(invoices))
                gif = len(list(gifts))
                pnt = len(list(points))
                if inv != 0 and gif != 0 and pnt != 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.dealer_id ='{}' AND invoices.redeemed='False'""".format(int(session["user_id"])))
                    gifts = conn.execute("""SELECT redemption.gift, redemption.date, users.first_name, users.last_name FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.dealer_id = {} AND redemption.gift_status != 'Fasle'""".format(session["user_id"]))
                    points = conn.execute("""SELECT users.first_name, users.last_name, SUM(invoices.points), invoices.plumber_id, users.redeem_request FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_approved = 'True' AND invoices.dealer_id = '{}' GROUP BY invoices.plumber_id""".format(session["user_id"]))
                    return render_template("index.html", invoices=invoices, gifts=gifts, points=points)
                elif inv == 0 and gif != 0 and pnt != 0:
                    gifts = conn.execute("""SELECT redemption.gift, redemption.date, users.first_name, users.last_name FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.dealer_id = {} AND redemption.gift_status != 'Fasle'""".format(session["user_id"]))
                    points = conn.execute("""SELECT users.first_name, users.last_name, SUM(invoices.points), invoices.plumber_id, users.redeem_request FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_approved = 'True' AND invoices.dealer_id = '{}' GROUP BY invoices.plumber_id""".format(session["user_id"]))
                    notif = "No pending invoices."
                    return render_template("index.html", notif=notif, gifts=gifts, points=points)
                elif inv != 0 and gif == 0 and pnt != 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.dealer_id ='{}' AND invoices.redeemed='False'""".format(int(session["user_id"])))
                    points = conn.execute("""SELECT users.first_name, users.last_name, SUM(invoices.points), invoices.plumber_id, users.redeem_request FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_approved = 'True' AND invoices.dealer_id = '{}' GROUP BY invoices.plumber_id""".format(session["user_id"]))
                    notif = "No gifts issued yet."
                    return render_template("index.html", notif=notif, invoices=invoices, points=points)
                elif inv == 0 and gif == 0 and pnt != 0:
                    notif = "No pending invoices or gifts issued."
                    return render_template("index.html", notif=notif, points=points)
                elif inv != 0 and gif != 0 and pnt == 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.dealer_id ='{}' AND invoices.redeemed='False'""".format(int(session["user_id"])))
                    gifts = conn.execute("""SELECT redemption.gift, redemption.date, users.first_name, users.last_name FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.dealer_id = {} AND redemption.gift_status != 'Fasle'""".format(session["user_id"]))
                    return render_template("index.html", invoices=invoices, gifts=gifts)
                if inv != 0 and gif == 0 and pnt == 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.dealer_id ='{}' AND invoices.redeemed='False'""".format(int(session["user_id"])))
                    notif = "No gifts issued."
                    return render_template("index.html", notif=notif, invoices=invoices)
                if inv == 0 and gif != 0 and pnt == 0:
                    gifts = conn.execute("""SELECT redemption.gift, redemption.date, users.first_name, users.last_name FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.dealer_id = {} AND redemption.gift_status != 'Fasle'""".format(session["user_id"]))
                    notif = "No pending invoices."
                    return render_template("index.html", notif=notif, gifts=gifts)
                if inv == 0 and gif == 0 and pnt == 0:
                    notif = "No pending invoices or gifts issued."
                    return render_template("index.html", notif=notif)

            elif session["type"] == "ACCOUNTS":
                invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.dealer_id = users.id WHERE invoices.points_calc ='{}'""".format("False"))
                if len(list(invoices)) != 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.dealer_id = users.id WHERE invoices.points_calc ='{}'""".format("False"))
                    return render_template("index.html", invoices=invoices)
                else:
                    notif = "All done! No invoices to process."
                    return render_template("index.html", notif=notif)

            elif session["type"] == "CHECKER":
                invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_calc = '{}' AND invoices.points_approved = '{}'""".format("True", "False"))
                redeem = conn.execute("""SELECT redemption.id, users.first_name, users.last_name, users.phone, redemption.points_requested, users.id FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.verify = 'False' AND redemption.gift_status = 'False'""")
                gift = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Approved'""")
                inv = len(list(invoices))
                red = len(list(redeem))
                gif = len(list(gift))
                if inv != 0 and red != 0 and gif != 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_calc = '{}' AND invoices.points_approved = '{}'""".format("True", "False"))
                    redeem = conn.execute("""SELECT redemption.id, users.first_name, users.last_name, users.phone, redemption.points_requested, users.id FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.verify = 'False' AND redemption.gift_status = 'False'""")
                    gift = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Approved'""")
                    return render_template("index.html", invoices=invoices, redeem=redeem, gift=gift)
                elif inv == 0 and red != 0 and gif != 0:
                    redeem = conn.execute("""SELECT redemption.id, users.first_name, users.last_name, users.phone, redemption.points_requested, users.id FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.verify = 'False' AND redemption.gift_status = 'False'""")
                    gift = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Approved'""")
                    return render_template("index.html", redeem=redeem, gift=gift)
                elif inv != 0 and red == 0 and gif != 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_calc = '{}' AND invoices.points_approved = '{}'""".format("True", "False"))
                    gift = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Approved'""")
                    return render_template("index.html", invoices=invoices, gift=gift)
                elif inv != 0 and red != 0 and gif == 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_calc = '{}' AND invoices.points_approved = '{}'""".format("True", "False"))
                    redeem = conn.execute("""SELECT redemption.id, users.first_name, users.last_name, users.phone, redemption.points_requested, users.id FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.verify = 'False' AND redemption.gift_status = 'False'""")
                    return render_template("index.html", invoices=invoices, redeem=redeem)
                elif inv == 0 and red == 0 and gif != 0:
                    gift = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Approved'""")
                    return render_template("index.html", gift=gift)
                elif inv == 0 and red != 0 and gif == 0:
                    redeem = conn.execute("""SELECT redemption.id, users.first_name, users.last_name, users.phone, redemption.points_requested, users.id FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.verify = 'False' AND redemption.gift_status = 'False'""")
                    return render_template("index.html", redeem=redeem)
                elif inv != 0 and red == 0 and gif == 0:
                    invoices = conn.execute("""SELECT * FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_calc = '{}' AND invoices.points_approved = '{}'""".format("True", "False"))
                    return render_template("index.html", invoices=invoices)
                elif inv == 0 and red == 0 and gif == 0:
                    notif = "All done! No pending work."
                    return render_template("index.html", notif=notif)

            elif session["type"] == "ADMIN":
                approval = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Selected'""")
                disburse = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Procured'""")
                app = len(list(approval))
                dis = len(list(disburse))
                if app != 0 and dis != 0:
                    approval = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Selected'""")
                    disburse = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Procured'""")
                    return render_template("index.html", approval=approval, disburse=disburse)
                elif app == 0 and dis != 0:
                    disburse = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Procured'""")
                    return render_template("index.html", disburse=disburse)
                elif app != 0 and dis == 0:
                    approval = conn.execute("""SELECT redemption.id, users.store_name, users.first_name, users.last_name, redemption.points_requested, redemption.gift FROM redemption JOIN users ON redemption.plumber_id = users.id WHERE redemption.gift_status = 'Selected'""")
                    return render_template("index.html", approval=approval)
                elif app == 0 and dis == 0:
                    notif = "All done! No pending approvals."
                    return render_template("index.html", notif=notif)

        return redirect("/")

    else:
        if session["type"] != "TRADER":
            with sqlite3.connect("plumber.db") as conn:
                if not request.form.get("red_id"):
                    conn.execute("""UPDATE invoices SET '{}' = "True", points = {} WHERE id = {}""".format(request.form.get("bool"), request.form.get("points"), request.form.get("invoice")))
                    conn.commit()
                else:
                    conn.execute("""UPDATE redemption SET gift = '{}', gift_status = '{}', verify = 'True' WHERE id = {}""".format(request.form.get("gift"), request.form.get("gift_status"), request.form.get("red_id")))
                    red_id = request.form.get("red_id")
                    if request.form.get("gift_status") == "Selected":
                        invoices = pd.read_sql_query("""SELECT invoices.id, invoices.points FROM invoices WHERE plumber_id = {} AND points_approved = 'True'""".format(request.form.get("plumber_id")), conn)
                        points = int(request.form.get("points"))
                        while points > 0:
                            for index, row in invoices.iterrows():
                                if row["points"] > 0:
                                    if row["points"] <= points:
                                        conn.execute("""UPDATE invoices SET points = 0, redemption_id = {}, redeemed = 'True' WHERE id = {}""".format(red_id, row["id"]))
                                        points -= row["points"]
                                    else:
                                        conn.execute("""UPDATE invoices SET points = {}, redemption_id = {}, redeemed = 'Partly' WHERE id = {}""".format((row["points"] - points), red_id, row["id"]))
                                        points -= points
                        conn.execute("""UPDATE redemption SET points_redeemed = {}, redeemed = 'True' WHERE id = {}""".format(int(request.form.get("points")), red_id))
                        conn.execute("""UPDATE users SET redeem_request = 'Approved' WHERE id = {}""".format(request.form.get("plumber_id")))
                        conn.commit()
                return redirect("/")
        else:
            with sqlite3.connect("plumber.db") as conn:
                try:
                    conn.execute("""UPDATE redemption SET gift = '{}', gift_status = '{}' WHERE id = {}""".format(request.form.get("gift"), request.form.get("gift_status"), request.form.get("red_id")))
                    conn.commit()
                except:
                    conn.execute("""INSERT INTO redemption (dealer_id, plumber_id, points_requested) VALUES(?, ?, ?)""", (request.form.get("dealer"), request.form.get("plumber"), request.form.get("points")))
                    conn.execute("""UPDATE users SET redeem_request = 'True' WHERE id = {}""".format(request.form.get("plumber")))
                    conn.commit()
                return redirect("/")


@app.route("/view_invoice")
@login_required
def view_invoice():
    if session["type"] == "ADMIN":
        with sqlite3.connect("plumber.db") as conn:
            traders = conn.execute("""SELECT users.store_name, SUM(invoices.amount) AS amount, SUM(invoices.points) AS points FROM invoices JOIN users ON invoices.dealer_id = users.id WHERE invoices.points_approved = 'True' AND invoices.redeemed = 'False' GROUP BY invoices.dealer_id""")
            plumbers = conn.execute("""SELECT users.first_name, users.last_name, users.store_name, SUM(invoices.amount) AS amount, SUM(invoices.points) AS points FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_approved = 'True' AND invoices.redeemed = 'False' GROUP BY invoices.plumber_id""")
            tr = len(list(traders))
            pl = len(list(plumbers))
            if tr != 0 and pl != 0:
                traders = conn.execute("""SELECT users.store_name, SUM(invoices.amount) AS amount, SUM(invoices.points) AS points FROM invoices JOIN users ON invoices.dealer_id = users.id WHERE invoices.points_approved = 'True' AND invoices.redeemed = 'False' GROUP BY invoices.dealer_id""")
                plumbers = conn.execute("""SELECT users.first_name, users.last_name, users.store_name, SUM(invoices.amount) AS amount, SUM(invoices.points) AS points FROM invoices JOIN users ON invoices.plumber_id = users.id WHERE invoices.points_approved = 'True' AND invoices.redeemed = 'False' GROUP BY invoices.plumber_id""")
                return render_template("view_invoice.html", traders=traders, plumbers=plumbers)
            else:
                notif = "No activity recorded."
                return render_template("view_invoice.html", notif=notif)


@app.route("/request_OTP", methods=["GET", "POST"])
def request_OTP():
    if request.method == "POST":
        phone = request.form.get("phone")

        with sqlite3.connect("plumber.db") as conn:
            registered = set(pd.read_sql_query("SELECT phone FROM users", conn)["phone"])
            if int(request.form.get("phone")) in registered:
                notif = "user already exists. try logging in"
                return render_template("request_OTP.html", notif=notif)

        number = str(phone)
        session["phone"] = phone
        val = sendSMS(number)
        return render_template("verify_OTP.html")
    else:
        return render_template("request_OTP.html")


@app.route("/verify_OTP", methods=["GET", "POST"])
def verify_OTP():
    if request.method == "POST":
        if str(request.form.get("OTP")) == str(session["OTP"]):
            try:
                if session["type"] == "TRADER":
                    return redirect("/plumber_register")
            except:
                return redirect("/trader_register")

        else:
            notif = "OTP is incorrect. Try again."
            return render_template("request_OTP.html", notif=notif)
    else:
        return render_template("verify_OTP.html")


def sendSMS(number): #Twilio
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    client = Client(account_sid, auth_token)
    OTP = randint(100001, 999999)
    session["OTP"] = OTP
    body = "Your OTP for registering on Customer Loyalty App is " + str(OTP)
    message = client.messages.create(from_=os.environ["FROM_NUMBER"], body=body, to=number)

    if message.sid:
        return True
    else:
        return False


# def sendSMS(number): #TextLocal
#     apikey = "oqo8RDC++Uo-kw1ejmJK0jc0piHLPi6RbMZoPKAXYh"
#     OTP = randint(100001, 999999)
#     session["OTP"] = OTP
#     print(OTP)
#     message = "Your OTP for registering on Customer Loyalty App is " + str(OTP)
#     data =  urllib.parse.urlencode({"apikey": apikey, "numbers": number,
#         "message" : message, "sender": "Jims Autos"})
#     data = data.encode("utf-8")
#     request = urllib.request.Request("https://api.textlocal.in/send/?")
#     f = urllib.request.urlopen(request, data)
#     fr = f.read()
#     return(fr)


@app.route("/trader_register", methods=["GET", "POST"])
def trader_register():
    if request.method == "POST":
        notif = None
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        store_name = request.form.get("store_name")

        with sqlite3.connect("plumber.db") as conn:
            registered = set(pd.read_sql_query("SELECT phone FROM users", conn)["phone"])
            try:
                if session["phone"]:
                    if not request.form.get("password"):
                        notif = "must provide a password"
                    elif password != confirm:
                        notif = "passwords don't match, try again"
                    elif not request.form.get("first_name"):
                        notif = "must provide first name"
                    elif not request.form.get("last_name"):
                        notif = "must provide surname"
                    elif not request.form.get("store_name"):
                        notif = "must provide store name"
                    else:
                        flash("Registration Successful! Login using your registered phone number.")
                        pass_hash = generate_password_hash(password)

                        conn.execute("INSERT INTO users (first_name, last_name, store_name, phone, hash) VALUES (?, ?, ?, ?, ?)", (first_name, last_name, store_name, session["phone"], pass_hash))

                        return redirect("/login")

                    return render_template("trader_register.html", notif=notif)
            except:
                return redirect("/request_OTP")

    elif request.method == "GET":
        return render_template("trader_register.html")


@app.route("/plumber_register", methods=["GET", "POST"])
@login_required
def plumber_register():
    if request.method == "POST":
        notif = None
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        phone = session["phone"]
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        dealer_id = int(session["user_id"])

        with sqlite3.connect("plumber.db") as conn:
            registered = set(pd.read_sql_query("SELECT phone FROM users", conn)["phone"])
            store = pd.read_sql_query("SELECT store_name FROM users WHERE id = '{}'".format(session["user_id"]), conn)
            if not request.form.get("password"):
                notif = "must provide a password"
            elif password != confirm:
                notif = "passwords don't match, try again"
            elif not request.form.get("first_name"):
                notif = "must provide first name"
            elif not request.form.get("last_name"):
                notif = "must provide surname"
            else:
                flash("Registration Successful! You may ask plumber to login using their registered phone number.")
                pass_hash = generate_password_hash(password)

                conn.execute("INSERT INTO users (first_name, last_name, store_name, phone, hash, dealer_id, type) VALUES (?, ?, ?, ?, ?, ?, ?)", (first_name, last_name, store["store_name"][0], phone, pass_hash, dealer_id, "PLUMBER"))

                return redirect("/")

            return render_template("plumber_register.html", notif=notif)

    elif request.method == "GET":
        return render_template("plumber_register.html")


def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return "." + (format if format != "jpeg" else "jpg")


@app.route("/uploads/<filename>")
@login_required
def send_file(filename):
    return send_from_directory(app.config["UPLOAD_PATH"], filename)


def make_unique(string):
    ident = uuid4().__str__()[:8]
    return f"{ident}-{string}"


@app.route("/invoice", methods=["POST", "GET"])
@login_required
def invoice():
    with sqlite3.connect("plumber.db") as conn:
        cursor = conn.cursor()
        plumbers_df = pd.read_sql_query("SELECT id, first_name, last_name FROM users WHERE dealer_id = '{}'".format(session["user_id"]), conn)
        plumbers = plumbers_df.T.to_dict().values()
    if request.method == "GET":
        if len(plumbers) != 0:
            return render_template("invoice.html", plumbers=plumbers)
        else:
            notif = "No plumbers registered. Please register the plumber first."
            return render_template("index.html", notif=notif)

    elif request.method == "POST":
        notif = None
        if not request.form.get("plumber"):
            notif = "Please select a plumber"
        elif not request.form.get("amount"):
            notif = "Please enter amount"
        elif "image" not in request.files:
            notif = "Please upload invoice"
        else:
            plumber = request.form.get("plumber")
            amount = request.form.get("amount")
            image_raw = request.files["image"]
            filename = secure_filename(image_raw.filename)
            if filename != "":
                file_ext = os.path.splitext(filename)[1]
                if file_ext not in app.config["UPLOAD_EXTENSIONS"] or \
                        file_ext != validate_image(image_raw.stream):
                    return "Invalid image", 400
                new_name = make_unique(filename)
                image_raw.save(os.path.join(app.config["UPLOAD_PATH"], new_name))
                image = new_name
                flash("Invoice submitted successfully!")

            cursor.execute("""INSERT INTO invoices (plumber_id, dealer_id, amount, image) VALUES (?, ?, ?, ?)""", (plumber, int(session["user_id"]), amount, image))
            conn.commit()

            return redirect("/")

        return render_template("invoice.html", notif=notif)


@app.route("/login", methods=["POST", "GET"])
def login():
    """Login user"""

    session.clear()

    if request.method == "POST":
        if not request.form.get("phone"):
            notif = "Must provide phone number."
            return render_template("login.html", notif=notif)
        elif not request.form.get("password"):
            notif = "Must provide password."
            return render_template("login.html", notif=notif)

        phone = request.form.get("phone")
        with sqlite3.connect("plumber.db") as conn:
            users = pd.read_sql_query("SELECT * FROM users WHERE phone = '{}'".format(phone), conn)

        if len(users.index) != 1 or not check_password_hash(users["hash"][0], request.form.get("password")):
            notif = "Invalid username or password."
            return render_template("login.html", notif=notif)

        session["user_id"] = users["id"][0]
        session["type"] = users["type"][0]
        session["phone"] = phone

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()

    return redirect("/")
