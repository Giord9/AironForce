from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta



app = Flask(__name__)
app.secret_key = "supersegreto"  # Cambia in produzione

# Sessione utente: 30 minuti di inattività
app.permanent_session_lifetime = timedelta(minutes=30)


@app.before_request
def ensure_admin_flag():
    if 'admin_logged_in' not in session:
        session['admin_logged_in'] = False

ADMIN_PASSWORD = "mypassword"  # Cambia in produzione con una password sicura
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.debug = True
app.config['DEBUG'] = True
app.config['ENV'] = 'development'
# DB config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# =========================
# MODELS
# =========================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

class Prenotazione(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    servizio = db.Column(db.String(50), nullable=False)
    giorno = db.Column(db.String(20), nullable=False)
    ora = db.Column(db.String(10), nullable=False)
    user = db.relationship('User', backref=db.backref('prenotazioni', lazy=True))

# =========================
# FILES (ancora usati per slot)
# =========================
SLOTS_FILE = os.path.join(BASE_DIR, "slots.json")
# (users/prenotazioni JSON non sono più necessari dopo migrazione, ma li teniamo per la migrazione)



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


# def migrate_json_to_db():
#     # Migrazione utenti
#     users = load_users()
#     for u in users:
#         if not User.query.filter_by(email=u['email']).first():
#             nuovo_user = User(email=u['email'], password=u['password'])
#             db.session.add(nuovo_user)

#     # Migrazione slot
#     slots = load_slots()
#     for s in slots:
#         if not Slot.query.filter_by(servizio=s['servizio'], giorno=s['giorno'], ora=s['ora']).first():
#             nuovo_slot = Slot(servizio=s['servizio'], giorno=s['giorno'], ora=s['ora'])
#             db.session.add(nuovo_slot)

#     # Migrazione prenotazioni
#     prenotazioni = load_prenotazioni()
#     for p in prenotazioni:
#         if not Prenotazione.query.filter_by(email=p['email'], servizio=p['servizio'], giorno=p['giorno'], ora=p['ora']).first():
#             nuova_prenotazione = Prenotazione(
#                 email=p['email'],
#                 servizio=p['servizio'],
#                 giorno=p['giorno'],
#                 ora=p['ora']
#             )
#             db.session.add(nuova_prenotazione)

#     db.session.commit()
#     print("✅ Migrazione completata!")


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

    # Carica tutti gli slot dal file JSON (che hai detto rimane per gli slot)
    all_slots = load_slots()

    filtered_slots = []

    for slot in all_slots:
        if slot['servizio'] != servizio:
            continue

        # Query per prendere le prenotazioni di questo slot dal DB
        prenotati_query = Prenotazione.query.filter_by(
            servizio=servizio,
            giorno=slot['giorno'],
            ora=slot['ora']
        ).all()

        prenotati_list = [p.user.email for p in prenotati_query]
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

        # Controlla se esiste già un utente con questa email
        if User.query.filter_by(email=email).first():
            return render_template("register.html", error="Email già registrata.")

        # Crea nuovo utente con password hashata
        password_hash = generate_password_hash(password)
        nuovo_user = User(email=email, password_hash=password_hash)
        db.session.add(nuovo_user)
        db.session.commit()

        # Salva sessione
        session['user'] = email
        return redirect(url_for('area_personale'))

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login utente"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.permanent = False  # Sessione scade dopo timeout
            session['user'] = email
            session['admin_logged_in'] = False  # forza disattivazione admin
            return redirect(url_for('area_personale'))

        return render_template("login.html", error="Credenziali errate.")

    return render_template("login.html")

@app.route('/logout')
def logout():
    """Logout utente"""
    session.pop('user', None)
    session['admin_logged_in'] = False
    return redirect(url_for('home'))

@app.route('/area_personale')
def area_personale():
    """Area personale utente con prenotazioni"""
    if 'user' not in session:
        flash("Sessione scaduta, effettua nuovamente il login.", "warning")
        return redirect(url_for('login'))

    user_email = session['user']
    user = User.query.filter_by(email=user_email).first()
    if not user:
        # Se per qualche motivo l'utente non esiste nel DB, logout forzato
        session.pop('user', None)
        return redirect(url_for('login'))

    prenotazioni_utente = Prenotazione.query.filter_by(user_id=user.id).all()

    return render_template("area_personale.html", prenotazioni=prenotazioni_utente, user=user_email)


# ==============================
#  PRENOTAZIONI SLOT
# ==============================

@app.route('/prenota_slot', methods=['POST'])
def prenota_slot():
    """API per prenotare uno slot"""
    if 'user' not in session:
        flash("Sessione scaduta, effettua nuovamente il login.", "warning")
        return redirect(url_for('login'))

    data = request.json
    email = session['user']
    servizio = data.get('servizio')
    giorno = data.get('giorno')
    ora = data.get('ora')

    if not (servizio and giorno and ora):
        return {"status": "error", "message": "Dati incompleti"}, 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return {"status": "error", "message": "Utente non trovato"}, 404

    # Controlli di disponibilità
    if servizio == 'funzionale':
        count = Prenotazione.query.filter_by(servizio=servizio, giorno=giorno, ora=ora).count()
        if count >= 6:
            return {"status": "error", "message": "Slot funzionale pieno"}, 409
    else:
        exists = Prenotazione.query.filter_by(servizio=servizio, giorno=giorno, ora=ora).first()
        if exists:
            return {"status": "error", "message": "Slot già prenotato"}, 409

    # Verifica prenotazione doppia per stesso utente
    doppia = Prenotazione.query.filter_by(servizio=servizio, giorno=giorno, ora=ora, user_id=user.id).first()
    if doppia:
        return {"status": "error", "message": "Hai già prenotato questo slot."}, 409

    # Salva prenotazione
    nuova_prenotazione = Prenotazione(user_id=user.id, servizio=servizio, giorno=giorno, ora=ora)
    db.session.add(nuova_prenotazione)
    db.session.commit()

    return {"status": "success"}

@app.route('/cancella_prenotazione', methods=['POST'])
def cancella_prenotazione():
    if 'user' not in session:
        flash("Sessione scaduta, effettua nuovamente il login.", "warning")
        return redirect(url_for('login'))

    data = request.json
    email = session['user']
    servizio = data.get('servizio')
    giorno = data.get('giorno')
    ora = data.get('ora')

    user = User.query.filter_by(email=email).first()
    if not user:
        return {"status": "error", "message": "Utente non trovato"}, 404

    prenotazione = Prenotazione.query.filter_by(
        user_id=user.id,
        servizio=servizio,
        giorno=giorno,
        ora=ora
    ).first()

    if prenotazione:
        db.session.delete(prenotazione)
        db.session.commit()
        return '', 200
    else:
        return {"status": "error", "message": "Prenotazione non trovata"}, 404

# ==============================
#  AREA ADMIN
# ==============================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login admin"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session.permanent = True  # Sessione resta finché non fa logout
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error="Password errata")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Logout admin"""
    session.pop('admin_logged_in', None)
    session['admin_logged_in'] = False
    return redirect(url_for('home'))

@app.route('/admin/panel')
@admin_required
def admin_panel():
    """Dashboard admin con lista slot e prenotazioni"""
    prenotazioni = Prenotazione.query.all()
    return render_template("admin_panel.html", slots=load_slots(), prenotazioni=prenotazioni)



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

with app.app_context():
    print("Creazione delle tabelle...")
    db.create_all()
    print("Tabelle create.")
    #migrate_json_to_db()  # Esegui una sola volta, poi puoi commentarla

if __name__ == "__main__":
    app.run(debug=True)