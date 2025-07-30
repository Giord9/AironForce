from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/servizi/<servizio>')
def servizio(servizio):
    nomi_servizi = {
        "1to1": "Allenamento Personal 1to1",
        "coppia": "Allenamento Personal di Coppia",
        "funzionale": "Allenamento Funzionale"
    }

    slot_settimanali = {
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

    nome = nomi_servizi.get(servizio, "Servizio")
    slot = slot_settimanali.get(servizio, {})

    return render_template("slots.html", nome=nome, slot_settimanali=slot)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)