from flask import Flask, request, jsonify, send_from_directory
import threading
import requests
import random
import time
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'chave-secreta-aescorp'

sessoes = {}

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

def enviar_pacote(ip, username, mensagem):
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
        requests.post("https://ngl.link/api/submit", json=payload, headers=headers)
    except:
        pass

def enviar_mensagens(ip):
    sessao = sessoes[ip]
    username = sessao["username"]
    mensagem = sessao["mensagem"]
    sessao["enviando"] = True
    sessao["enviadas"] = 0
    sessao["total"] = 100

    def disparar():
        while sessao["enviadas"] < sessao["total"] and sessao["enviando"]:
            threading.Thread(target=enviar_pacote, args=(ip, username, mensagem)).start()
            sessao["enviadas"] += 1
            time.sleep(0.01)  # menor delay possível

    threads = []
    for _ in range(5):  # 5 threads simultâneas atirando
        t = threading.Thread(target=disparar)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    sessao["enviando"] = False

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
        return jsonify(status="Nenhum dado encontrado."), 400
    if sessoes[ip]["enviando"]:
        return jsonify(status="Já enviando."), 400

    thread = threading.Thread(target=enviar_mensagens, args=(ip,))
    thread.start()

    return jsonify(status="Disparo iniciado.")

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
