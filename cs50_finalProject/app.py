from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from helpers import login_required
import datetime
import sqlite3
import requests

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'super secret key'
Session(app)

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        con = sqlite3.connect('test.db')
        cur = con.cursor()
        if request.form.get("age"):
            cur.execute("INSERT OR REPLACE INTO profile VALUES(?, ?, ?, ?, ?, ?, ?);", 
                        (session['user_id'], request.form.get("age"), request.form.get("gender"), request.form.get("height"), request.form.get("weight"), request.form.get("activitylevel"), 
                        request.form.get("goal")))
        else:
            cur.execute("INSERT OR REPLACE INTO diet_goal VALUES(?, ?, ?, ?, ?);", 
                            (session['user_id'], request.form.get("calories"), request.form.get("protein"), request.form.get("fat"), request.form.get("carbs")))
        con.commit()
        cur.close()
        return redirect("/")
    else:
        con = sqlite3.connect('test.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        res = cur.execute("SELECT * FROM profile INNER JOIN diet_goal ON profile.user_id = diet_goal.user_id WHERE profile.user_id = ?;", (session['user_id'], )).fetchone()
        if 'calories' not in session:
            try: 
                session['calories'] = res['calories']
                session['protein'] = res['protein']
                session['fat'] = res['fat']
                session['carbs'] = res['carbs']
            except:
                print("Goal not set yet")
        return render_template("index.html",res=res)


    

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        #Query db for matching username and pw
        con = sqlite3.connect('test.db')
        cur = con.cursor()
        res = cur.execute("SELECT * FROM users WHERE username = ?;",(request.form.get("email"), )).fetchall()
        cur.close()
        if len(res) != 1 :
            print("Username doesnt exist")
        elif check_password_hash(res[0][2], request.form.get("password")):
            session["user_id"] = res[0][0]
            session["email"] = res[0][1]
            return redirect("/")
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
        cur.close()
    return render_template("root.html")

@app.route("/search")
def search():

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
        dic = {}
        if request.args.get("date") != str(datetime.date.today()) and request.args.get("date") != None:
            print(request.args.get("date"))
            day = request.args.get("date")
            date  = f"{day}%"
        else:
            date = f"{datetime.date.today()}%"
            dic['today'] = True
        con = sqlite3.connect('test.db')
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        res = cur.execute("""SELECT * FROM entries INNER JOIN diet ON entries.entry_id = diet.diet_id 
                            WHERE user_id = ? AND time LIKE ? ORDER BY time DESC;""", (session["user_id"], date)).fetchall()
        res2 = cur.execute("""SELECT SUM(calories), SUM(carbohydrates_total_g), SUM(protein_g), SUM(cholesterol_mg), SUM(fat_total_g), SUM(fat_saturated_g), SUM(fiber_g),
                            SUM(sugar_g), SUM(sodium_mg), SUM(potassium_mg) FROM entries INNER JOIN diet ON entries.entry_id = diet.diet_id 
                            WHERE user_id = ? AND time LIKE ?;""", (session["user_id"], date)).fetchone()
        cur.close()
        
        if res:
            dic['header_list'] = res[0].keys()
            dic['query_rows'] = res
            dic['total_counts'] = res2
            dic['date'] = date[:-1]
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

@app.route("/macros", methods=["GET", "POST"])
@login_required
def macros():
    if request.method == "POST":
        print(request.form.get('goal'))
        print(request.form.get('gender'))
        print(request.form.get('weight'))
        print(request.form.to_dict())
        

        url = "https://fitness-calculator.p.rapidapi.com/macrocalculator"

        querystring = request.form.to_dict()
       

        headers = {
            'x-rapidapi-key': "12610bb9b7mshfeae823b3448922p17ed51jsndac5f877f999",
            'x-rapidapi-host': "fitness-calculator.p.rapidapi.com"
            }

        response = requests.request("GET", url, headers=headers, params=querystring).json()

        print(response)
        return render_template("macros.html", res = response)
    return render_template("macros.html")


@app.route("/bookings", methods=["GET", "POST"])
@login_required
def bookings():
    if request.method == "POST":
        datetime =''
        con = sqlite3.connect('test.db')
        cur = con.cursor()
        #if delete in form, remove entry from courses_log else inser into log
        if "delete" in request.form.get('course'):
            course_code = request.form.get('course')[7:]

            cur.execute("DELETE FROM courses_log WHERE (user_id = ? AND course_id = ?);",(session["user_id"], course_code ))
            cur.execute("UPDATE courses SET slots = slots + 1 WHERE course_id = ?;",(course_code, ))

        else:
            startTime =  request.form.get('startTime')
            endTime =  request.form.get('endTime')
            #sanity check to see if clash, clash needs to be empty list for no clash
            clash = cur.execute(""" SELECT * FROM courses INNER JOIN courses_log ON courses.course_id = courses_log.course_id WHERE (courses.start_time < ? AND courses.end_time > ?) AND courses_log.user_id = ?;""", (endTime, startTime, session["user_id"])).fetchall()
            print(clash)
            if not clash:
                cur.execute("INSERT INTO courses_log(user_id, course_id) VALUES (?, ?);",(session["user_id"], request.form.get('course') ))
                cur.execute("UPDATE courses SET slots = slots - 1 WHERE course_id = ?;",(request.form.get('course'), ))
            else:
                print("CLASHED")
                flash('Course will clash with your timetable')               
        con.commit()
        cur.close()
        return redirect("/bookings")
    if request.method == "GET":
        con = sqlite3.connect('test.db')
        cur = con.cursor()
        res={}
        res['courses'] = cur.execute("""SELECT * FROM courses WHERE course_id NOT IN(SELECT courses.course_id FROM courses INNER JOIN courses_log ON courses.course_id = courses_log.course_id WHERE courses_log.user_id = ?);""",(session["user_id"], )).fetchall()
        res['booked'] = cur.execute("""SELECT * FROM courses WHERE course_id IN(SELECT courses.course_id FROM courses INNER JOIN courses_log ON courses.course_id = courses_log.course_id WHERE courses_log.user_id = ?);""",(session["user_id"], )).fetchall()
        res['courseList'] = ['EE2002', 'EE3001', 'EE4717', 'EE8888', 'EE9999' ]
        
        for course in res['courseList']:
            res[course] = cur.execute("""SELECT users.username, courses_log.course_id, courses_log.time FROM users INNER JOIN courses_log ON users.id = courses_log.user_id WHERE courses_log.course_id = ? ;""",(course, )).fetchall()

        cur.close()
        
        return render_template("bookings.html", res=res)


