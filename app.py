from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = "supersegreto"  # Cambia in produzione

ADMIN_PASSWORD = "mypassword"  # Cambia in produzione con una password sicura
SLOTS_FILE = 'slots.json'
USERS_FILE = "users.json"
PRENOTAZIONI_FILE = 'prenotazioni.json'

# ==============================
#  FUNZIONI UTILI (utility functions)
# ==============================

def load_slots():
    """Carica gli slot disponibili dal file JSON"""
    if not os.path.exists(SLOTS_FILE):
        return []
    with open(SLOTS_FILE, 'r') as f:
        return json.load(f)

def save_slots(slots):
    """Salva gli slot disponibili nel file JSON"""
    with open(SLOTS_FILE, 'w') as f:
        json.dump(slots, f, indent=2, ensure_ascii=False)

def load_users():
    """Carica gli utenti registrati"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return []

def save_users(users):
    """Salva gli utenti registrati"""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_prenotazioni():
    """Carica le prenotazioni dal file"""
    if not os.path.exists(PRENOTAZIONI_FILE):
        return []
    with open(PRENOTAZIONI_FILE, 'r') as f:
        return json.load(f)

def save_prenotazioni(data):
    """Salva le prenotazioni sul file"""
    with open(PRENOTAZIONI_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def admin_required(f):
    """Decorator per permettere accesso solo ad admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def mask_email(email):
    """Oscura parte dell'email per privacy."""
    nome, dominio = email.split('@')
    if len(nome) > 2:
        nome = nome[0] + '*'*(len(nome)-2) + nome[-1]
    else:
        nome = nome[0] + '*'
    return nome + '@' + dominio


# ==============================
#  ROTTE PUBBLICHE (visibili a tutti)
# ==============================

@app.route("/")
def home():
    """Pagina iniziale"""
    return render_template("index.html")

@app.route("/chi-siamo")
def chi_siamo():
    """Pagina 'Chi Siamo'"""
    return render_template("chi_siamo.html")

@app.route('/servizi/<servizio>')
def servizio(servizio):
    """Mostra gli slot disponibili per un determinato servizio"""
    is_admin = session.get('admin_logged_in', False)

    nomi_servizi = {
        "1to1": "Allenamento Personal 1to1",
        "Coppia": "Allenamento Personal di Coppia",
        "funzionale": "Allenamento Funzionale"
    }

    coach_name = "Raffaella Esposito"
    all_slots = load_slots()
    prenotazioni = load_prenotazioni()
    filtered_slots = []

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

        # Se l'utente NON è admin, oscura le email
        if not is_admin:
            prenotati_list = [mask_email(email) for email in prenotati_list]

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

    return render_template("slots.html", nome=nome, slot_settimanali=filtered_slots, utente_autenticato=utente_autenticato, servizio=servizio, is_admin=is_admin)


# ==============================
#  AUTENTICAZIONE UTENTE
# ==============================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registrazione nuovo utente"""
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
    """Login utente"""
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

@app.route('/logout')
def logout():
    """Logout utente"""
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/area_personale')
def area_personale():
    """Area personale utente con prenotazioni"""
    if 'user' not in session:
        return redirect(url_for('login'))

    user_email = session['user']
    prenotazioni_utente = [p for p in load_prenotazioni() if p['email'] == user_email]

    return render_template("area_personale.html", prenotazioni=prenotazioni_utente, user=user_email)


# ==============================
#  PRENOTAZIONI SLOT
# ==============================

@app.route('/prenota_slot', methods=['POST'])
def prenota_slot():
    """API per prenotare uno slot"""
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

    # Controlli di disponibilità
    if servizio == 'funzionale':
        if sum(1 for p in prenotazioni if p['servizio'] == servizio and p['giorno'] == giorno and p['ora'] == ora) >= 6:
            return {"status": "error", "message": "Slot funzionale pieno"}, 409
    else:
        if any(p['servizio'] == servizio and p['giorno'] == giorno and p['ora'] == ora for p in prenotazioni):
            return {"status": "error", "message": "Slot già prenotato"}, 409

    # Verifica prenotazione doppia per stesso utente
    if any(p['servizio'] == servizio and p['giorno'] == giorno and p['ora'] == ora and p['email'] == email for p in prenotazioni):
        return {"status": "error", "message": "Hai già prenotato questo slot."}, 409

    # Salva prenotazione
    prenotazioni.append({'email': email, 'servizio': servizio, 'giorno': giorno, 'ora': ora})
    save_prenotazioni(prenotazioni)

    return {"status": "success"}

@app.route('/cancella_prenotazione', methods=['POST'])
def cancella_prenotazione():
    """Cancella una prenotazione dell'utente"""
    if 'user' not in session:
        return redirect(url_for('login'))

    email = session['user']
    servizio = request.form.get('servizio')
    giorno = request.form.get('giorno')
    ora = request.form.get('ora')

    nuove_prenotazioni = [
        p for p in load_prenotazioni()
        if not (p['email'] == email and p['servizio'] == servizio and p['giorno'] == giorno and p['ora'] == ora)
    ]

    save_prenotazioni(nuove_prenotazioni)
    flash("Prenotazione cancellata con successo.")
    return redirect(url_for('area_personale'))


# ==============================
#  AREA ADMIN
# ==============================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login admin"""
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
    """Logout admin"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin/panel')
@admin_required
def admin_panel():
    """Dashboard admin con lista slot e prenotazioni"""
    return render_template("admin_panel.html", slots=load_slots(), prenotazioni=load_prenotazioni())

@app.route('/admin/add_slot', methods=['POST'])
@admin_required
def add_slot():
    """Aggiungi nuovo slot"""
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
    """Modifica o elimina slot"""
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


# ==============================
#  AVVIO APP
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
