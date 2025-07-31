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

@app.route('/servizi/<servizio>')
def servizio(servizio):
    nomi_servizi = {
        "1to1": "Allenamento Personal 1to1",
        "coppia": "Allenamento Personal di Coppia",
        "funzionale": "Allenamento Funzionale"
    }

    coach_name = "Raffaella Esposito"  # il nome fisso del coach

    all_slots = load_slots()
    filtered_slots = []
    for slot in all_slots:
        if slot['servizio'] == servizio:
            filtered_slots.append({
                'giorno': slot['giorno'],
                'ora': slot['ora'],
                'coach': coach_name
            })

    nome = nomi_servizi.get(servizio, "Servizio")

    return render_template("slots.html", nome=nome, slots=filtered_slots)
    
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
