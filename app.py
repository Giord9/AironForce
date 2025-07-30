from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def carica_slots():
    if os.path.exists("slots.json"):
        with open("slots.json", "r") as f:
            return json.load(f)
    return []

def salva_slots(slots):
    with open("slots.json", "w") as f:
        json.dump(slots, f, indent=4)

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

    slots = carica_slots()
    slot_settimanali = {}
    for slot in slots:
        if slot["servizio"] == servizio:
            giorno = slot["giorno"]
            ora = slot["ora"]
            slot_settimanali.setdefault(giorno, []).append(ora)

    nome = nomi_servizi.get(servizio, "Servizio")
    return render_template("slots.html", nome=nome, slot_settimanali=slot_settimanali)

# --- ADMIN LOGIN ---

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "password123":  # Cambia password in modo sicuro!
            session["logged_in"] = True
            return redirect(url_for("admin_panel"))
        else:
            return "Credenziali errate", 401
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("logged_in", None)
    return redirect(url_for("home"))

# --- ADMIN PANEL ---

@app.route("/admin/panel")
def admin_panel():
    if not session.get("logged_in"):
        return redirect(url_for("admin_login"))
    slots = carica_slots()
    return render_template("admin_panel.html", slots=slots)

# --- AGGIUNGI SLOT ---

@app.route("/admin/add_slot", methods=["POST"])
def add_slot():
    if not session.get("logged_in"):
        return redirect(url_for("admin_login"))

    servizio = request.form.get("servizio")
    giorno = request.form.get("giorno")
    ora = request.form.get("ora")

    if not (servizio and giorno and ora):
        return "Dati slot incompleti", 400

    slots = carica_slots()
    slots.append({"servizio": servizio, "giorno": giorno, "ora": ora})
    salva_slots(slots)

    return redirect(url_for("admin_panel"))

# --- MODIFICA/ELIMINA SLOT ---

@app.route("/admin/edit_slot/<int:idx>", methods=["POST"])
def edit_slot(idx):
    if not session.get("logged_in"):
        return redirect(url_for("admin_login"))

    slots = carica_slots()
    if idx < 0 or idx >= len(slots):
        return "Indice slot non valido", 400

    action = request.form.get("action")
    if action == "modifica":
        servizio = request.form.get("servizio")
        giorno = request.form.get("giorno")
        ora = request.form.get("ora")
        if not (servizio and giorno and ora):
            return "Dati slot incompleti", 400
        slots[idx] = {"servizio": servizio, "giorno": giorno, "ora": ora}
    elif action == "elimina":
        slots.pop(idx)
    else:
        return "Azione non riconosciuta", 400

    salva_slots(slots)
    return redirect(url_for("admin_panel"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
