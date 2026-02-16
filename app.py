from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "secretkey"

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# -------------------- INIT DB --------------------
def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER,
            completed_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------------------- ROUTES --------------------

@app.route('/')
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username,password) VALUES (?,?)",
                         (username,password))
            conn.commit()
            return redirect("/login")
        except:
            return "Username already exists!"
        finally:
            conn.close()

    return render_template("register.html")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?",
                            (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session["user_id"] = user['id']
            return redirect("/dashboard")
        else:
            return "Invalid credentials!"

    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    habits = conn.execute("SELECT * FROM habits WHERE user_id=?",
                          (session["user_id"],)).fetchall()

    habit_data = []

    for habit in habits:
        completions = conn.execute(
            "SELECT * FROM completions WHERE habit_id=? ORDER BY completed_date DESC",
            (habit['id'],)
        ).fetchall()

        streak = 0
        today = date.today()

        for comp in completions:
            comp_date = datetime.strptime(comp['completed_date'], "%Y-%m-%d").date()
            if comp_date == today:
                streak += 1
                today = today.replace(day=today.day-1)
            else:
                break

        habit_data.append({
            "id": habit['id'],
            "name": habit['name'],
            "streak": streak
        })

    conn.close()

    return render_template("dashboard.html", habits=habit_data)

@app.route('/add_habit', methods=['POST'])
def add_habit():
    if "user_id" not in session:
        return redirect("/login")

    name = request.form['habit']

    conn = get_db()
    conn.execute("INSERT INTO habits (user_id,name) VALUES (?,?)",
                 (session["user_id"],name))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route('/complete/<int:habit_id>')
def complete(habit_id):
    today = date.today().strftime("%Y-%m-%d")

    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM completions WHERE habit_id=? AND completed_date=?",
        (habit_id,today)
    ).fetchone()

    if not existing:
        conn.execute(
            "INSERT INTO completions (habit_id,completed_date) VALUES (?,?)",
            (habit_id,today)
        )
        conn.commit()

    conn.close()
    return redirect("/dashboard")

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
