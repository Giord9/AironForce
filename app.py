from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'secret_key_change_this'  # per sessione login

DATA_FILE = 'slots.json'

# Carica slot da file JSON (o crea default)
def load_slots():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # dati di default se file non esiste
        return {
            "1to1": {
                "Lunedì": ["10:00", "11:00", "16:00", "17:00"],
                "Mercoledì": ["10:00", "11:00", "16:00", "17:00"],
                "Venerdì": ["10:00", "11:00", "16:00", "17:00"],
                "Sabato": ["10:00", "11:00", "16:00", "17:00"],
            },
            "coppia": {
                "Martedì": ["18:00", "19:00"],
                "Giovedì": ["18:00", "19:00"],
            },
            "funzionale": {
                "Lunedì": ["19:00"],
                "Mercoledì": ["20:00"],
            }
        }

# Salva slot su file JSON
def save_slots(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Login semplice (username: admin, password: password)
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'password':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Credenziali errate')
    return render_template('admin_login.html')

# Logout admin
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

# Pannello admin per modificare slot
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    slots = load_slots()

    if request.method == 'POST':
        servizio = request.form.get('servizio')
        giorno = request.form.get('giorno')
        orario = request.form.get('orario')

        if servizio and giorno and orario:
            if servizio not in slots:
                slots[servizio] = {}
            if giorno not in slots[servizio]:
                slots[servizio][giorno] = []
            if orario not in slots[servizio][giorno]:
                slots[servizio][giorno].append(orario)
                slots[servizio][giorno].sort()

            save_slots(slots)

    return render_template('admin_panel.html', slots=slots)

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

    slots = load_slots()
    slot_settimanali = slots.get(servizio, {})

    nome = nomi_servizi.get(servizio, "Servizio")

    return render_template("slots.html", nome=nome, slot_settimanali=slot_settimanali)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
