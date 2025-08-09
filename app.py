from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash  # <--- import per hash password

app = Flask(__name__)
app.secret_key = "una_chiave_super_segreta"  # cambia con una tua chiave segreta

ADMIN_PASSWORD = "mypassword"  # cambia con una password sicura

SLOTS_FILE = 'slots.json'
USERS_FILE = 'users.json'  # <--- file utenti

# --- Funzioni per utenti ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

# --- Funzioni per slots ---
def load_slots():
    if not os.path.exists(SLOTS_FILE):
        return []
    with open(SLOTS_FILE, 'r') as f:
        return json.load(f)

def save_slots(slots):
    with open(SLOTS_FILE, 'w') as f:
        json.dump(slots, f, indent=2, ensure_ascii=False)

# --- Decorator admin ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotte ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        users = load_users()
        if any(u['email'] == email for u in users):
            return render_template("register.html", error="Email già registrata.")
        hashed_password = generate_password_hash(password)  # hash della password
        users.append({'email': email, 'password': hashed_password})
        save_users(users)
        session['user'] = email
        return redirect(url_for('area_personale'))
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        users = load_users()
        user = next((u for u in users if u['email'] == email), None)
        if user and check_password_hash(user['password'], password):
            session['user'] = email
            return redirect(url_for('area_personale'))
        return render_template("login.html", error="Credenziali non valide.")
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/area_personale')
def area_personale():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_email = session['user']
    prenotazioni = load_prenotazioni()

    prenotazioni_utente = [p for p in prenotazioni if p['email'] == user_email]

    return render_template("area_personale.html", prenotazioni=prenotazioni_utente, user=user_email)

# --- Funzioni per prenotazioni ---
PRENOTAZIONI_FILE = 'prenotazioni.json'

def load_prenotazioni():
    if not os.path.exists(PRENOTAZIONI_FILE):
        return []
    with open(PRENOTAZIONI_FILE, 'r') as f:
        return json.load(f)

def save_prenotazioni(data):
    with open(PRENOTAZIONI_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ... (resto del codice invariato) ...

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
