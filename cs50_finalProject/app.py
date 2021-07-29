from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from helpers import login_required
import sqlite3
import requests
import time

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'super secret key'
Session(app)

@app.route("/")
@login_required
def index():
    
        
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        #Query db for matching username and pw
        con = sqlite3.connect('test.db')
        cur = con.cursor()
        res = cur.execute("SELECT * FROM users WHERE username = ?;",(request.form.get("email"), )).fetchall()
        # res = [ id, username, hash]
        print(type(res))
        print(res)
        if len(res) != 1 :
            print("Username doesnt exist")
        elif check_password_hash(res[0][2], request.form.get("password")):
            session["user_id"] = res[0][0]
            session["email"] = res[0][1]
            msg = f"Logged in as {res[0][1]}, session_id = {session['user_id']}"
            print(msg)
            return render_template("index.html", msg=msg)
        else:
            print("Password incorrect")
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        #Push username and hashed password
        con = sqlite3.connect('test.db')
        cur = con.cursor()
        cur.execute("INSERT INTO users (username,hash) VALUES (?, ?);", (request.form.get("email"), generate_password_hash(request.form.get("password"))))
        con.commit()
        print("REGISTERING")
        print(request.form.get("email"))
        print(request.form.get("password"))
        print(generate_password_hash(request.form.get("password")))
        print(request.form.get("action"))
        
    return render_template("root.html")

@app.route("/search")
def search():
    print("CALLED")
    url = "https://calorieninjas.p.rapidapi.com/v1/nutrition"
    query = request.args.get("search")
    querystring = {"query":f"{query}"}
    print(querystring)
    headers = {
        'x-rapidapi-key': "12610bb9b7mshfeae823b3448922p17ed51jsndac5f877f999",
        'x-rapidapi-host': "calorieninjas.p.rapidapi.com"
        }

    response = requests.request("GET", url, headers=headers, params=querystring).json()
    response = response.get("items")[0]
    print(response)
    return render_template("search.html",response=response)

@app.route("/diet", methods=["GET", "POST"])
@login_required
def diet():
    if request.method == "GET":
        con = sqlite3.connect('test.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        res = cur.execute("""SELECT * FROM entries INNER JOIN diet ON entries.entry_id = diet.diet_id 
                            WHERE user_id = ? AND time>= (SELECT datetime('now','start of day'));""", (session["user_id"], )).fetchall()
        res2 = cur.execute("""SELECT SUM(calories), SUM(carbohydrates_total_g), SUM(protein_g), SUM(cholesterol_mg), SUM(fat_total_g), SUM(fat_saturated_g), SUM(fiber_g),
                            SUM(sugar_g), SUM(sodium_mg), SUM(potassium_mg) FROM entries INNER JOIN diet ON entries.entry_id = diet.diet_id 
                            WHERE user_id = ? AND time>= (SELECT datetime('now','start of day'));""", (session["user_id"], )).fetchall()
        cur.close()
        dic = {}
        if res:
            dic['header_list'] = res[0].keys()
            dic['query_rows'] = res
            dic['total_counts'] = res2
        print(len(res2))
        print(tuple(res2[0]))
        return render_template("diet.html", dic=dic) 
        
    if request.method == "POST":
        food = request.form.get("food")
        servings = request.form.get("servings")
        con = sqlite3.connect('test.db')
        cur = con.cursor()
        cur.execute("INSERT INTO entries (food,servings,user_id) VALUES (?, ? ,?);",(food, servings, session["user_id"]))

        url = "https://calorieninjas.p.rapidapi.com/v1/nutrition"
        querystring = {"query":f"{food}"}
        print(querystring)
        headers = {
            'x-rapidapi-key': "12610bb9b7mshfeae823b3448922p17ed51jsndac5f877f999",
            'x-rapidapi-host': "calorieninjas.p.rapidapi.com"
            }

        res = requests.request("GET", url, headers=headers, params=querystring).json()
        res = res.get("items")[0]
        for key in res:
            if key == 'name':
                continue
            res[key] = round(res[key] * float(servings), 2)
        cur.execute("INSERT INTO diet VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",(cur.lastrowid, res['calories'], res['carbohydrates_total_g'],  res['protein_g'], res['cholesterol_mg'],
        res['fat_total_g'], res['fat_saturated_g'], res['fiber_g'], res['sugar_g'], res['sodium_mg'], res['potassium_mg']))
        con.commit()
        cur.close()
        return redirect("/diet")

        # con.row_factory = sqlite3.Row
        # cur = con.cursor()
        # res = cur.execute("SELECT * FROM entries INNER JOIN diet ON entries.entry_id = diet.diet_id WHERE user_id = ? AND time>= (SELECT datetime('now','start of day'));", (session["user_id"], )).fetchall()
        # cur.close()
        # msg = f"You have added {servings} servings of {food} to your diet today."
        # dic = {}
        # dic['header_list'] = res[0].keys()
        # dic['query_rows'] = res
        # dic['msg'] = msg
    


