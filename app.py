from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from functools import wraps
import sqlite3
import re
import requests
import concurrent.futures
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS live_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            gateway TEXT,
            card_number TEXT,
            response TEXT,
            bin TEXT,
            brand TEXT,
            card_type TEXT,
            bank TEXT,
            country TEXT,
            credits_charged INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS bin_cache (
            bin TEXT PRIMARY KEY,
            brand TEXT,
            card_type TEXT,
            bank TEXT,
            country TEXT,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def _brand_from_digit(digits):
    if not digits:
        return "Unknown"
    first = digits[0]
    if first == "4":
        return "VISA"
    if first in ("5", "2"):
        return "Mastercard"
    if first == "3":
        return "Amex"
    if first == "6":
        return "Discover"
    return "Unknown"

def _cache_get(bin_num):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT brand, card_type, bank, country FROM bin_cache WHERE bin = ?", (bin_num,))
    row = c.fetchone()
    conn.close()
    return row

def _cache_set(bin_num, brand, card_type, bank, country):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO bin_cache (bin, brand, card_type, bank, country, cached_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (bin_num, brand, card_type, bank, country))
    conn.commit()
    conn.close()

def lookup_bin(card_number):
    digits = re.sub(r"\D", "", card_number)
    if len(digits) < 6:
        return {
            "bin": digits,
            "brand": "Unknown",
            "card_type": "Unknown",
            "bank": "Unknown",
            "country": "Unknown"
        }

    bin_num = digits[:6]

    cached = _cache_get(bin_num)
    if cached:
        return {
            "bin": bin_num,
            "brand": cached[0] or "Unknown",
            "card_type": cached[1] or "Unknown",
            "bank": cached[2] or "Unknown",
            "country": cached[3] or "Unknown"
        }

    brand = _brand_from_digit(digits)
    card_type = "Unknown"
    bank = "Unknown"
    country = "Unknown"

    try:
        resp = requests.get(
            "https://lookup.binlist.net/" + bin_num,
            timeout=3,
            headers={
                "Accept-Version": "3",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        )
        if resp.status_code == 200:
            data = resp.json()
            brand = (data.get("scheme") or brand).upper()
            card_type = (data.get("type") or "Unknown").capitalize()
            bank_data = data.get("bank") or {}
            bank = bank_data.get("name") or "Unknown"
            country_data = data.get("country") or {}
            country_name = country_data.get("name") or "Unknown"
            country_emoji = country_data.get("emoji") or ""
            country_alpha = (country_data.get("alpha2") or "").lower()
            if country_name != "Unknown":
                country = country_name
                if country_alpha:
                    country += " " + country_alpha
                if country_emoji:
                    country = country_emoji + " " + country
    except Exception:
        pass

    _cache_set(bin_num, brand, card_type, bank, country)

    return {
        "bin": bin_num,
        "brand": brand,
        "card_type": card_type,
        "bank": bank,
        "country": country
    }

def save_live_card(user_id, gateway, card_number, response, credits_charged=3):
    info = lookup_bin(card_number)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO live_cards
        (user_id, gateway, card_number, response, bin, brand, card_type, bank, country, credits_charged)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, gateway, card_number, response,
        info["bin"], info["brand"], info["card_type"], info["bank"], info["country"],
        credits_charged
    ))
    conn.commit()
    conn.close()

def get_live_cards(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, gateway, card_number, response, bin, brand, card_type, bank, country, credits_charged, created_at
        FROM live_cards
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_live_card(user_id, card_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM live_cards WHERE id = ? AND user_id = ?", (card_id, user_id))
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

@app.route("/live")
@login_required
def live():
    cards = get_live_cards(session["user_id"])
    return render_template("live.html", username=session.get("username"), cards=cards)

@app.route("/live/delete/<int:card_id>", methods=["POST"])
@login_required
def live_delete(card_id):
    delete_live_card(session["user_id"], card_id)
    return jsonify({"ok": True})

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
    telegram_username = "@" + user[1] + "_tg"
    telegram_id = "612345678"
    telegram_active = True
    return render_template(
        "settings.html",
        username=user[1],
        member_since=member_since,
        telegram_username=telegram_username,
        telegram_id=telegram_id,
        telegram_active=telegram_active,
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

@app.route("/prices")
@login_required
def prices():
    return render_template("prices.html", username=session.get("username"))

@app.route("/gateways", methods=["GET"])
@login_required
def gateways():
    gateway_list = get_gateway_list()
    proxy_count = 0
    try:
        from checkers import stripe_park
        proxy_count = stripe_park.get_proxy_count()
    except Exception:
        pass
    return jsonify({
        "gateways": gateway_list,
        "proxy_count": proxy_count
    })

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
    if result.get("status") == "alive":
        gateways_list = get_gateway_list()
        gw_name = next((g["name"] for g in gateways_list if g["id"] == gateway_id), gateway_id)
        response_text = result.get("redirects_to") or result.get("error") or "Approved"
        try:
            save_live_card(session["user_id"], gw_name, url, response_text, 3)
        except Exception:
            pass
    return jsonify(result)

@app.route("/check-batch", methods=["POST"])
@login_required
def check_batch():
    data = request.get_json()
    cards = data.get("cards", [])
    gateway_id = data.get("gateway", "").strip()
    workers = int(data.get("workers", 5))
    if not cards:
        return jsonify({"error": "No cards"}), 400
    if not gateway_id:
        return jsonify({"error": "No gateway selected"}), 400
    workers = max(1, min(10, workers))
    cards = cards[:20]
    gateways_list = get_gateway_list()
    gw_name = next((g["name"] for g in gateways_list if g["id"] == gateway_id), gateway_id)
    user_id = session["user_id"]

    def process_one(card):
        try:
            result = run_check(gateway_id, card)
        except Exception as e:
            return {"url": card, "status": "error", "error": str(e)[:150]}
        if result.get("status") == "alive":
            response_text = result.get("redirects_to") or result.get("error") or "Approved"
            try:
                save_live_card(user_id, gw_name, card, response_text, 3)
            except Exception:
                pass
        return result

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(process_one, cards))

    return jsonify({"results": results})

init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)