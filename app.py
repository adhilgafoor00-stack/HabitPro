from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            category TEXT,
            created_at TEXT
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

# ---------------- HOME ----------------
@app.route('/')
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return redirect("/login")


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        created_at = date.today().strftime("%Y-%m-%d")

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username,password,created_at) VALUES (?,?,?)",
                (username, password, created_at)
            )
            conn.commit()
            return redirect("/login")
        except:
            return "Username already exists!"
        finally:
            conn.close()

    return render_template("register.html")


# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session["user_id"] = user['id']
            return redirect("/dashboard")
        else:
            return "Invalid Credentials"

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    habits = conn.execute(
        "SELECT * FROM habits WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    total = len(habits)

    today_str = date.today().strftime("%Y-%m-%d")

    today_count = conn.execute('''
        SELECT COUNT(*) FROM completions
        JOIN habits ON habits.id = completions.habit_id
        WHERE habits.user_id=? AND completed_date=?
    ''', (session["user_id"], today_str)).fetchone()[0]

    percent = int((today_count / total) * 100) if total > 0 else 0

    # Weekly Data
    weekly = []
    for i in range(6, -1, -1):
        day = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        count = conn.execute('''
            SELECT COUNT(*) FROM completions
            JOIN habits ON habits.id = completions.habit_id
            WHERE habits.user_id=? AND completed_date=?
        ''', (session["user_id"], day)).fetchone()[0]
        weekly.append(count)

    habit_data = []

    for habit in habits:
        completions = conn.execute(
            "SELECT completed_date FROM completions WHERE habit_id=? ORDER BY completed_date DESC",
            (habit['id'],)
        ).fetchall()

        # Proper streak calculation
        streak = 0
        current_day = date.today()

        completed_dates = [datetime.strptime(c['completed_date'], "%Y-%m-%d").date() for c in completions]

        while current_day in completed_dates:
            streak += 1
            current_day -= timedelta(days=1)

        habit_data.append({
            "id": habit['id'],
            "name": habit['name'],
            "category": habit['category'],
            "streak": streak
        })

    conn.close()

    return render_template("dashboard.html",
                           habits=habit_data,
                           total=total,
                           today=today_count,
                           percent=percent,
                           weekly=weekly)


# ---------------- ADD HABIT ----------------
@app.route('/add_habit', methods=['POST'])
def add_habit():
    if "user_id" not in session:
        return redirect("/login")

    name = request.form['habit']
    category = request.form['category']
    created_at = date.today().strftime("%Y-%m-%d")

    conn = get_db()
    conn.execute(
        "INSERT INTO habits (user_id,name,category,created_at) VALUES (?,?,?,?)",
        (session["user_id"], name, category, created_at)
    )
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- COMPLETE ----------------
@app.route('/complete/<int:id>')
def complete(id):
    today = date.today().strftime("%Y-%m-%d")

    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM completions WHERE habit_id=? AND completed_date=?",
        (id, today)
    ).fetchone()

    if not existing:
        conn.execute(
            "INSERT INTO completions (habit_id,completed_date) VALUES (?,?)",
            (id, today)
        )
        conn.commit()

    conn.close()
    return redirect("/dashboard")


# ---------------- DELETE ----------------
@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM habits WHERE id=?", (id,))
    conn.execute("DELETE FROM completions WHERE habit_id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")


# ---------------- EDIT ----------------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db()

    if request.method == "POST":
        name = request.form['name']
        category = request.form['category']
        conn.execute(
            "UPDATE habits SET name=?, category=? WHERE id=?",
            (name, category, id)
        )
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    habit = conn.execute("SELECT * FROM habits WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("edit.html", habit=habit)


# ---------------- PROFILE ----------------
@app.route('/profile')
def profile():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()
    conn.close()

    return render_template("profile.html", user=user)


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)

