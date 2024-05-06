from flask import Flask, request, render_template, redirect, url_for
import pyodbc
import requests
import uuid
import json

app = Flask(__name__, template_folder='templates')

# Paramètres de connexion à la base de données
conn_string = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:server-tpgestion.database.windows.net,1433;Database=db-gestion;Uid=user;Pwd=Password01;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

# Clés Azure Translator
translator_key = "13bd2e5c30544d81af470009e8476f67"
endpoint = "https://api.cognitive.microsofttranslator.com"
location = "switzerlandnorth"

@app.route('/')
def index():
    conn = pyodbc.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Vocabulaire")
    mots = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', mots=mots)

@app.route('/add', methods=['POST'])
def add():
    francais = request.form['francais']
    conn = pyodbc.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Vocabulaire (Francais) VALUES (?)", francais)
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/translate', methods=['POST'])
def translate():
    id = request.form['id']
    conn = pyodbc.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute("SELECT Francais FROM Vocabulaire WHERE ID=?", id)
    text = cursor.fetchone()[0]

    # Appel à Azure Translator
    path = '/translate'
    url = endpoint + path
    
    params = {
        'api-version': '3.0',
        'from': 'fr',
        'to': 'en'
    }
    
    headers = {
        'Ocp-Apim-Subscription-Key': translator_key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }
    body = [{
        'text': text
        }]
    response = requests.post(url, params=params, headers=headers, json=body)

    # Vérifier si la réponse est réussie
    if response.status_code == 200:
        translated_text = response.json()[0]['translations'][0]['text']
        cursor.execute("UPDATE Vocabulaire SET Anglais=? WHERE ID=?", translated_text, id)
        conn.commit()
    else:
        # En cas d'erreur dans la traduction, imprimer le message d'erreur
        print("Failed to translate text. HTTP status code:", response.status_code)

    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete():
    id = request.form['id']
    conn = pyodbc.connect(conn_string)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Vocabulaire WHERE ID=?", id)
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)