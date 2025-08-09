from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = "supersegreto"  # Cambialo in produzione

USERS_FILE = "users.json"

# Funzioni per gestione utenti
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

# Rotta home
@app.route('/')
def home():
    return render_template("index.html")

# Registrazione
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        users = load_users()

        if any(u['email'] == email for u in users):
            return render_template("register.html", error="Email già registrata.")

        users.append({'email': email, 'password': password})
        save_users(users)
        session['user'] = email
        return redirect(url_for('area_personale'))

    return render_template("register.html")

# Login utente
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        users = load_users()

        for u in users:
            if u['email'] == email and u['password'] == password:
                session['user'] = email
                return redirect(url_for('area_personale'))
        return render_template("login.html", error="Credenziali errate.")

    return render_template("login.html")

# Area personale
@app.route('/area_personale')
def area_personale():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("area_personale.html", user=session['user'])

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('admin', None)
    return redirect(url_for('home'))

# Login admin
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "admin123":  # Cambiala in produzione
            session['admin'] = True
            return redirect(url_for('area_admin'))
        else:
            return render_template("admin_login.html", error="Password errata.")
    return render_template("admin_login.html")

# Area admin
@app.route('/area_admin')
def area_admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return "<h1>Benvenuto nell'area admin!</h1>"

if __name__ == "__main__":
    app.run(debug=True)
