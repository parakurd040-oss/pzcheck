app_code = '''from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from functools import wraps
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from checkers import get_gateway_list, run_check

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key"

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash, created_at FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash, created_at FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(username, password_hash):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
    conn.commit()
    conn.close()

def update_password(user_id, new_hash):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not username or not password:
            flash("Username and password are required", "error")
        elif len(username) < 3:
            flash("Username must be at least 3 characters", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters", "error")
        elif password != confirm:
            flash("Passwords do not match", "error")
        elif get_user_by_username(username):
            flash("Username already exists", "error")
        else:
            password_hash = generate_password_hash(password)
            create_user(username, password_hash)
            user = get_user_by_username(username)
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash("Registration successful! Welcome!", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = get_user_by_username(username)
        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username"))

@app.route("/settings")
@login_required
def settings():
    user = get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))
    member_since = "Unknown"
    if user[3]:
        try:
            dt = datetime.strptime(user[3].split(".")[0], "%Y-%m-%d %H:%M:%S")
            member_since = dt.strftime("%b %Y")
        except Exception:
            member_since = user[3][:7]
    return render_template(
        "settings.html",
        username=user[1],
        member_since=member_since,
        active_tab=request.args.get("tab", "account")
    )

@app.route("/settings/password", methods=["POST"])
@login_required
def change_password():
    current = request.form.get("current_password", "")
    new = request.form.get("new_password", "")
    confirm = request.form.get("confirm_password", "")
    user = get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))
    if not current or not new or not confirm:
        flash("All fields are required", "error")
    elif not check_password_hash(user[2], current):
        flash("Current password is incorrect", "error")
    elif len(new) < 6:
        flash("New password must be at least 6 characters", "error")
    elif new != confirm:
        flash("New passwords do not match", "error")
    elif new == current:
        flash("New password must be different from current", "error")
    else:
        update_password(user[0], generate_password_hash(new))
        flash("Password updated successfully", "success")
    return redirect(url_for("settings", tab="account"))

@app.route("/gateways", methods=["GET"])
@login_required
def gateways():
    return jsonify(get_gateway_list())

@app.route("/check", methods=["POST"])
@login_required
def check():
    data = request.get_json()
    url = data.get("url", "").strip()
    gateway_id = data.get("gateway", "").strip()
    if not url:
        return jsonify({"error": "Input is empty"}), 400
    if not gateway_id:
        return jsonify({"error": "No gateway selected"}), 400
    result = run_check(gateway_id, url)
    return jsonify(result)

init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
'''

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

print("app.py written successfully.")