from flask import Flask, render_template, request, redirect, Response, send_from_directory
from datetime import datetime
import csv
import os
import base64

app = Flask(__name__)

NOMI = ["Davide", "Federico", "Luca", "Giorgia", "Roberto", "Rayssa", "Nuovo"]

ADMIN_USER = "silvio.pomi@webidoo.com"
ADMIN_PASS = "123456@@"

@app.route("/static/<path:path>")
def static_file(path):
    return send_from_directory("static", path)

def check_auth(auth):
    if not auth:
        return False
    try:
        decoded = base64.b64decode(auth.split(" ")[-1]).decode("utf-8")
        username, password = decoded.split(":")
        return username == ADMIN_USER and password == ADMIN_PASS
    except:
        return False

@app.route("/timbratura", methods=["GET", "POST"])
def timbratura():
    messaggio = ""
    if request.method == "POST":
        nome = request.form.get("nome")
        azione = request.form.get("azione")
        lat = request.form.get("lat")
        lon = request.form.get("lon")
        oggi = datetime.now().strftime("%Y-%m-%d")
        ora = datetime.now().strftime("%H:%M:%S")
        trovato = False

        if os.path.exists("timbrature.csv"):
            with open("timbrature.csv", newline="") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 3 and row[0] == nome and row[1].startswith(oggi) and row[2] == azione:
                        trovato = True
                        break

        if trovato:
            messaggio = f"Errore: {azione} già registrata oggi per {nome}."
        else:
            with open("timbrature.csv", "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([nome, f"{oggi} {ora}", azione, lat, lon])
            messaggio = f"{azione.capitalize()} registrata per {nome} alle {ora}"

    return render_template("timbratura.html", nomi=NOMI, messaggio=messaggio)

@app.route("/admin")
def admin():
    auth = request.headers.get("Authorization")
    if not check_auth(auth):
        return Response("Accesso non autorizzato", 401, {"WWW-Authenticate": 'Basic realm="Login"'})

    timbrature = {nome: [] for nome in NOMI}
    if os.path.exists("timbrature.csv"):
        with open("timbrature.csv", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3 and row[0] in timbrature:
                    timbrature[row[0]].append((row[1], row[2]))

    return render_template("admin.html", timbrature=timbrature)

if __name__ == '__main__':
    app.run(debug=True)
