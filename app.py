from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

# Funzione per caricare gli slot dal file JSON
def load_slots():
    try:
        with open("slots.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Funzione per salvare gli slot nel file JSON
def save_slots(slots):
    with open("slots.json", "w", encoding="utf-8") as f:
        json.dump(slots, f, ensure_ascii=False, indent=2)

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

    nome = nomi_servizi.get(servizio, "Servizio")

    slots = load_slots()

    # Organizza gli slot per giorno
    slot_settimanali = {}
    for slot in slots:
        if slot["servizio"] == servizio:
            giorno = slot["giorno"]
            ora = slot["ora"]
            slot_settimanali.setdefault(giorno, []).append(ora)

    return render_template("slots.html", nome=nome, slot_settimanali=slot_settimanali)

# --- Admin routes ---

@app.route('/admin/panel', methods=['GET'])
def admin_panel():
    slots = load_slots()
    return render_template("admin_panel.html", slots=slots)

@app.route('/admin/add_slot', methods=['POST'])
def add_slot():
    servizio = request.form.get('servizio')
    giorno = request.form.get('giorno')
    ora = request.form.get('ora')

    slots = load_slots()
    slots.append({"servizio": servizio, "giorno": giorno, "ora": ora})
    save_slots(slots)
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit_slot/<int:idx>', methods=['POST'])
def edit_slot(idx):
    action = request.form.get('action')
    slots = load_slots()

    if 0 <= idx < len(slots):
        if action == 'modifica':
            servizio = request.form.get('servizio')
            giorno = request.form.get('giorno')
            ora = request.form.get('ora')
            slots[idx] = {"servizio": servizio, "giorno": giorno, "ora": ora}
            save_slots(slots)
        elif action == 'elimina':
            slots.pop(idx)
            save_slots(slots)

    return redirect(url_for('admin_panel'))

@app.route('/admin/logout')
def admin_logout():
    # Per ora solo redirect alla home, poi potrai aggiungere login vero
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
