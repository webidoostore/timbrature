from flask import Flask, render_template_string, request, redirect, Response
from datetime import datetime
import csv
import os
import base64

app = Flask(__name__)

NOMI = ["Davide", "Federico", "Luca", "Giorgia", "Roberto", "Rayssa", "Nuovo"]

ADMIN_USER = "silvio.pomi@webidoo.com"
ADMIN_PASS = "123456@@"

template_timbratura = """
<!doctype html>
<html>
<head>
  <title>Timbratura</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body { font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; }
    .container { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; max-width: 400px; width: 90%; }
    h2 { color: #0055A4; margin-bottom: 20px; }
    select, textarea { width: 100%; padding: 10px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #ccc; font-size: 16px; }
    button { background: #0077D9; color: white; padding: 12px 20px; margin: 5px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; }
    button:hover { background: #0055A4; }
    img { max-width: 150px; margin-bottom: 20px; }
    .note-box { margin-bottom: 15px; }
  </style>
</head>
<body>
  <div class="container">
    <img src="https://webidoostore.com/cdn/shop/files/store_whitec_2_200x@2x.png?v=1681913975" alt="Logo Webidoo">
    <h2>Timbratura Entrata/Uscita</h2>
    <form method="post">
      <select name="nome">
        {% for nome in nomi %}
          <option value="{{ nome }}">{{ nome }}</option>
        {% endfor %}
      </select>
      <div class="note-box">
        <textarea name="note" placeholder="Aggiungi note se sei in ritardo... (opzionale)"></textarea>
      </div>
      <button name="azione" value="entrata">Timbra Entrata</button>
      <button name="azione" value="uscita">Timbra Uscita</button>
    </form>
    {% if messaggio %}<p>{{ messaggio }}</p>{% endif %}
  </div>
</body>
</html>
"""

template_admin = """
<!doctype html>
<html>
<head>
  <title>Admin - Riepilogo Mensile</title>
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    nav { margin-bottom: 20px; }
    nav a { margin-right: 15px; text-decoration: none; color: #0077D9; font-weight: bold; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    th, td { padding: 8px; border: 1px solid #ccc; text-align: left; }
    h3 { margin-top: 40px; color: #0055A4; }
  </style>
</head>
<body>
  <h2>Riepilogo Completo per il Mese</h2>
  <nav>
    {% for nome in timbrature.keys() %}
      <a href="#{{ nome }}">{{ nome }}</a>
    {% endfor %}
  </nav>
  {% for nome, records in timbrature.items() %}
  <h3 id="{{ nome }}">{{ nome }}</h3>
  <table>
    <tr><th>Data e Ora</th><th>Azione</th><th>Note</th></tr>
    {% for r in records %}
    <tr><td>{{ r[0] }}</td><td>{{ r[1] }}</td><td>{{ r[2] if r|length > 2 else '' }}</td></tr>
    {% endfor %}
  </table>
  {% endfor %}
</body>
</html>
"""

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
        note = request.form.get("note", "")
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
                writer.writerow([nome, f"{oggi} {ora}", azione, note])
            messaggio = f"{azione.capitalize()} registrata per {nome} alle {ora}"

    return render_template_string(template_timbratura, nomi=NOMI, messaggio=messaggio)

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
                    timbrature[row[0]].append((row[1], row[2], row[3] if len(row) > 3 else ""))

    return render_template_string(template_admin, timbrature=timbrature)

if __name__ == '__main__':
    app.run(debug=True)
