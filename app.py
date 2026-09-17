from flask import Flask, jsonify, request
import os
import requests

app = Flask(__name__)

# URL da API FastAPI da calculadora.
# Se a variável CALCULADORA_URL não existir,
# será usado o endereço local padrão.
CALCULADORA_URL = os.getenv(
    "CALCULADORA_URL",
    "http://localhost:8000/api/CalculaNota"
)


@app.route("/")
def home():
    return jsonify({
        "projeto": "Radar ENEM",
        "disciplina": "Computacao em Nuvem",
        "status": "online"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/aluno/<nome>")
def aluno(nome):
    ambiente = os.getenv("AMBIENTE", "desenvolvimento")

    return jsonify({
        "aluno": nome,
        "ambiente": ambiente,
        "mensagem": "Bem-vindo ao Mini Radar ENEM"
    })


# Rota antiga: consulta uma nota individual.
# Mantida para preservar a funcionalidade do projeto anterior.
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


# Nova rota: chama a calculadora FastAPI.
@app.route("/exibir_nota", methods=["POST"])
def exibir_nota():
    dados_aluno = request.json

    try:
        resposta = requests.post(
            CALCULADORA_URL,
            json={
                "notas": dados_aluno.get("notas")
            },
            timeout=2.0
        )

        resposta.raise_for_status()
        resultado = resposta.json()

        return jsonify({
            "mensagem": (
                f"Sua nota de corte é: "
                f"{resultado['nota_corte_calculada']}"
            )
        }), 200

    except requests.exceptions.Timeout:
        return jsonify({
            "erro": (
                "A calculadora está com alta demanda neste momento. "
                "Continue lendo as notícias do portal e tente novamente "
                "em alguns minutos."
            )
        }), 503

    except requests.exceptions.ConnectionError:
        return jsonify({
            "erro": (
                "Calculadora temporariamente indisponível. "
                "Nossos engenheiros já estão atuando!"
            )
        }), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)