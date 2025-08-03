from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = "una_chiave_super_segreta"  # cambia con una tua chiave segreta

ADMIN_PASSWORD = "mypassword"  # cambia con una password sicura

SLOTS_FILE = 'slots.json'

def load_slots():
    if not os.path.exists(SLOTS_FILE):
        return []
    with open(SLOTS_FILE, 'r') as f:
        return json.load(f)

def save_slots(slots):
    with open(SLOTS_FILE, 'w') as f:
        json.dump(slots, f, indent=2, ensure_ascii=False)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chi-siamo")
def chi_siamo():
    return render_template("chi_siamo.html")

@app.route('/servizi/<servizio>')
def servizio(servizio):
    nomi_servizi = {
        "1to1": "Allenamento Personal 1to1",
        "Coppia": "Allenamento Personal di Coppia",
        "funzionale": "Allenamento Funzionale"
    }

    coach_name = "Raffaella Esposito"

    all_slots = load_slots()
    filtered_slots = []
    prenotazioni = load_prenotazioni()

    for slot in all_slots:
        if slot['servizio'] != servizio:
            continue

        prenotati_list = [
            p['email'] for p in prenotazioni
            if p['servizio'] == servizio and p['giorno'] == slot['giorno'] and p['ora'] == slot['ora']
        ]

        count = len(prenotati_list)

        # logica stato
        stato = 'prenotato' if (servizio != 'funzionale' and count > 0) or (servizio == 'funzionale' and count >= 6) else 'disponibile'

        filtered_slots.append({
            'giorno': slot['giorno'],
            'ora': slot['ora'],
            'coach': coach_name,
            'stato': stato,
            'prenotati': count,
            'lista_prenotati': prenotati_list
        }) 
           
    nome = nomi_servizi.get(servizio, "Servizio")
    utente_autenticato = 'user' in session
    is_admin = session.get('admin_logged_in', False)

    return render_template("slots.html", nome=nome, slot_settimanali=filtered_slots, utente_autenticato=utente_autenticato,servizio=servizio,is_admin=is_admin)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error="Password errata")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin/panel')
@admin_required
def admin_panel():
    slots = load_slots()
    return render_template("admin_panel.html", slots=slots)

@app.route('/admin/add_slot', methods=['POST'])
@admin_required
def add_slot():
    servizio = request.form.get('servizio')
    giorno = request.form.get('giorno')
    ora = request.form.get('ora')

    if not (servizio and giorno and ora):
        flash("Compila tutti i campi!", "error")
        return redirect(url_for('admin_panel'))

    slots = load_slots()
    slots.append({'servizio': servizio, 'giorno': giorno, 'ora': ora})
    save_slots(slots)

    flash("Slot aggiunto con successo!", "success")
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit_slot/<int:idx>', methods=['POST'])
@admin_required
def edit_slot(idx):
    action = request.form.get('action')
    slots = load_slots()

    if idx < 0 or idx >= len(slots):
        flash("Slot non trovato", "error")
        return redirect(url_for('admin_panel'))

    if action == 'modifica':
        servizio = request.form.get('servizio')
        giorno = request.form.get('giorno')
        ora = request.form.get('ora')

        if not (servizio and giorno and ora):
            flash("Compila tutti i campi!", "error")
            return redirect(url_for('admin_panel'))

        slots[idx] = {'servizio': servizio, 'giorno': giorno, 'ora': ora}
        save_slots(slots)
        flash("Slot modificato con successo!", "success")

    elif action == 'elimina':
        slots.pop(idx)
        save_slots(slots)
        flash("Slot eliminato con successo!", "success")

    return redirect(url_for('admin_panel'))
  
  # --- Gestione utenti ---

def load_users():
    if not os.path.exists("users.json"):
        return []
    with open("users.json", "r") as f:
        return json.load(f)

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        users = load_users()
        user = next((u for u in users if u['email'] == email and u['password'] == password), None)
        if user:
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

PRENOTAZIONI_FILE = 'prenotazioni.json'

def load_prenotazioni():
    if not os.path.exists(PRENOTAZIONI_FILE):
        return []
    with open(PRENOTAZIONI_FILE, 'r') as f:
        return json.load(f)

def save_prenotazioni(data):
    with open(PRENOTAZIONI_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route('/prenota_slot', methods=['POST'])
def prenota_slot():
    if 'user' not in session:
        return redirect(url_for('login'))

    data = request.json
    email = session['user']
    servizio = data.get('servizio')
    giorno = data.get('giorno')
    ora = data.get('ora')

    if not (servizio and giorno and ora):
        return {"status": "error", "message": "Dati incompleti"}, 400

    prenotazioni = load_prenotazioni()

    # Verifica se l'utente ha già prenotato questo slot
    for p in prenotazioni:
        if p['servizio'] == servizio and p['giorno'] == giorno and p['ora'] == ora and p['email'] == email:
            return {"status": "error", "message": "Hai già prenotato questo slot."}, 409

    if servizio == 'funzionale':
        # Conta quante persone hanno già prenotato questo slot
        count = sum(1 for p in prenotazioni if p['servizio'] == servizio and p['giorno'] == giorno and p['ora'] == ora)
        if count >= 6:
            return {"status": "error", "message": "Slot funzionale pieno"}, 409
    else:
        # Per 1to1 o coppia: nessuno deve aver prenotato
        for p in prenotazioni:
            if p['servizio'] == servizio and p['giorno'] == giorno and p['ora'] == ora:
                return {"status": "error", "message": "Slot già prenotato"}, 409

    # Salva la prenotazione
    prenotazioni.append({
        'email': email,
        'servizio': servizio,
        'giorno': giorno,
        'ora': ora
    })
    save_prenotazioni(prenotazioni)

    return {"status": "success"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
