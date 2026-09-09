from flask import Flask, jsonify
import os
import requests

url = "http://localhost:5000/nota/650"
for _ in range(1000): requests.get(url)
print("Requisições concluídas")


app = Flask(__name__)
@app.route("/")
def home():
 return jsonify({
 "projeto": "Radar ENEM",
 "disciplina": "Computacao em Nuvem",
 "status": "online"
 })
@app.route("/health")
def health():
 return jsonify({"status": "healthy"})
@app.route("/aluno/<nome>")
def aluno(nome):
    ambiente = os.getenv("AMBIENTE", "desenvolvimento")
    return jsonify({
        "aluno": nome,
        "ambiente": ambiente,
    "mensagem": "Bem-vindo ao Mini Radar ENEM"
 })

 
@app.route("/nota/<int:nota>")
def consultar_nota(nota):
    if nota >= 600:
        classificacao = "acima de 600"
    else:
        classificacao = "abaixo de 600"
    return jsonify({
        "nota": nota,
        "classificacao": classificacao
 })
    
if __name__ == "__main__":
 app.run(host="0.0.0.0", port=5000)
