from flask import Flask, request, jsonify, send_from_directory, render_template_string
import threading
import requests
import random
import time
import os
import string
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'chave-secreta-aescorp'

# Armazena sessões por IP
sessoes = {}

# Funções de utilidade
def gerar_device_id():
    return str(uuid4())

def gerar_user_agent():
    agentes = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (Linux; Android 10)",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
    ]
    return random.choice(agentes) + f" AppleWebKit/{random.randint(500, 599)}.36 (KHTML, like Gecko) Chrome/{random.randint(80, 105)}.0.{random.randint(1000, 4999)}.100 Safari/{random.randint(500, 599)}.36"

# Função de envio em thread
def enviar_mensagens(ip):
    sessao = sessoes[ip]
    username = sessao["username"]
    mensagem = sessao["mensagem"]
    sessao["enviando"] = True
    sessao["enviadas"] = 0
    sessao["total"] = 100

    for i in range(100):
        if not sessao["enviando"]:
            break

        payload = {
            "username": username,
            "question": mensagem,
            "deviceId": gerar_device_id()
        }

        headers = {
            "User-Agent": gerar_user_agent(),
            "Content-Type": "application/json"
        }

        try:
            res = requests.post("https://ngl.link/api/submit", json=payload, headers=headers)
            if res.status_code == 429:
                time.sleep(random.uniform(3, 5))  # bloqueado, espera mais
            else:
                sessao["enviadas"] += 1
        except Exception:
            pass

        time.sleep(random.uniform(0.5, 1.5))

    sessao["enviando"] = False

# Rotas
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def css():
    return send_from_directory('.', 'style.css')

@app.route('/atualizar', methods=['POST'])
def atualizar():
    ip = request.remote_addr
    username = request.form.get('username')
    mensagem = request.form.get('mensagem')

    sessoes[ip] = {
        "username": username,
        "mensagem": mensagem,
        "enviando": False,
        "enviadas": 0,
        "total": 100
    }

    return jsonify(status="Dados atualizados.")

@app.route('/enviar', methods=['POST'])
def enviar():
    ip = request.remote_addr

    if ip not in sessoes:
        return jsonify(status="Nenhum dado encontrado. Atualize o formulário."), 400

    if sessoes[ip]["enviando"]:
        return jsonify(status="Envio já em andamento."), 400

    thread = threading.Thread(target=enviar_mensagens, args=(ip,))
    thread.start()

    return jsonify(status="Envio iniciado.")

@app.route('/parar', methods=['POST'])
def parar():
    ip = request.remote_addr
    if ip in sessoes:
        sessoes[ip]["enviando"] = False
        return jsonify(status="Envio interrompido.")
    return jsonify(status="Nenhum envio ativo.")

@app.route('/progresso')
def progresso():
    ip = request.remote_addr
    if ip in sessoes:
        return jsonify(
            enviadas=sessoes[ip]["enviadas"],
            total=sessoes[ip]["total"]
        )
    return jsonify(enviadas=0, total=100)

if __name__ == '__main__':
    app.run(debug=True)
