# Radar ENEM — Resultados dos testes de carga (10.000 usuários)

Data: 17/09/2026 · Máquina: Linux, 20 CPUs, 30 GB RAM, Docker Desktop 29.7 · Locust 2.46.5 · uvicorn 0.53 · FastAPI 0.141

Parâmetros iguais em todos os testes: **10.000 usuários**, spawn rate 500/s, duração 2 min,
`wait_time = between(1, 3)`, rota `POST /exibir_nota` (fluxo Locust → Flask → FastAPI),
Locust rodando com `--processes 8` (um processo só não aguenta 10k usuários).

---

## 1. Correções feitas antes de rodar

| Arquivo | Problema | Correção |
|---|---|---|
| `locustfile.py` | Batia em `/api/CalculaNota` (direto na FastAPI). O relatório diz `/exibir_nota`. | Trocado para `/exibir_nota`. |
| `docker-compose.yml` | `host.docker.internal` não resolve em Linux. | Adicionado `extra_hosts: ["host.docker.internal:host-gateway"]`. No Windows/Mac não faz diferença. |
| `docker-compose.yml` | Container Flask esgota portas efêmeras a >500 conexões/s. | Adicionado `sysctls` (`ip_local_port_range`, `tcp_tw_reuse`). |
| `Dockerfile` / `requirements.txt` | `python app.py` sobe o dev server do werkzeug (sem keep-alive, backlog 128). Com 10k usuários ele é o gargalo e mascara os workers da FastAPI (ver seção 2). | CMD trocado para **gunicorn** (8 processos × 64 threads, keep-alive, backlog 4096). `gunicorn` adicionado ao requirements. |
| `locustfile_lb.py` | Usa `self.client_id`, que não existe em `HttpUser` → `AttributeError`. | Não corrigido (não é usado no relatório). Trocar por `id(self)` se for usar. |

Scripts adicionados: `fastapi.sh <workers>` (reinicia a FastAPI no host), `rodar_teste.sh <nome>` (roda o Locust headless e salva CSV em `resultados/`), `resumo.py` (resume um CSV).

---

## 2. Primeira tentativa: Flask com dev server (`python app.py`) — como estava no projeto

| Métrica | 1 worker | 4 workers |
|---|---|---|
| Número de usuários | 10.000 | 10.000 |
| Total de requisições | 66.272 | 67.162 |
| Requisições por segundo | 551 | 559 |
| Requisições com falha | 14.497 (21,9%) | 15.296 (22,8%) |
| Tempo médio | 2.622 ms | 2.823 ms |
| Mediana | 380 ms | 380 ms |
| Percentil 95 | 11.000 ms | 11.000 ms |
| Erros | 14.176 × `Connection reset by peer`, 321 × HTTP 503 | 15.240 × `Connection reset by peer`, 56 × HTTP 503 |

**Conclusão:** resultado idêntico com 1 e 4 workers. As falhas são `Connection reset` do próprio Flask
(backlog de 128 conexões do servidor de desenvolvimento estourou), e não HTTP 503 (timeout da calculadora).
A única coisa que mudou foi o número de 503 (321 → 56), mostrando que a FastAPI melhorou, mas o gargalo
estava antes dela. **Com o dev server do Flask, o teste não mede os workers da FastAPI.**
Por isso o Flask foi trocado por gunicorn para os testes da seção 3.

---

## 3. Teste oficial: Flask com gunicorn

### 3.1 Teste de carga com 1 worker (`uvicorn main:app --port 8000 --workers 1`)

| Métrica | Resultado com 1 worker |
|---|---|
| Número de usuários | 10.000 |
| Total de requisições | 92.784 |
| Requisições por segundo | 771 |
| Requisições com falha | 0 (0%) |
| Tempo médio | 7.437 ms |
| Mediana | 8.200 ms |
| Percentil 95 | 8.500 ms |

**Análise:** 771 RPS bate exatamente no teto teórico de 1 worker: o endpoint é `def` síncrono com
`time.sleep(0.05)`, então roda no threadpool padrão do Starlette (40 threads) → 40 / 0,05 s = **800 req/s**.
Não houve 503 porque cada chamada Flask → FastAPI ainda ficou abaixo do timeout de 2 s; a fila se formou
antes, no backlog do gunicorn — por isso a mediana de 8,2 s. O sistema está saturado, mas não falha.

### 3.2 Teste de carga com 4 workers (`uvicorn main:app --port 8000 --workers 4`)

| Métrica | Resultado com 4 workers |
|---|---|
| Número de usuários | 10.000 |
| Total de requisições | 236.076 |
| Requisições por segundo | 1.962 |
| Requisições com falha | 0 (0%) |
| Tempo médio | 1.786 ms |
| Mediana | 1.600 ms |
| Percentil 95 | 2.800 ms |

### 3.3 Comparação

| Métrica | 1 worker | 4 workers | Variação |
|---|---|---|---|
| RPS | 771 | 1.962 | **+154 % (2,5×)** |
| Falhas | 0 | 0 | — |
| Tempo médio | 7.437 ms | 1.786 ms | **−76 %** |
| Mediana | 8.200 ms | 1.600 ms | **−80 %** |
| P95 | 8.500 ms | 2.800 ms | **−67 %** |

**Análise:** com 4 workers a capacidade teórica da FastAPI sobe para 4 × 800 = 3.200 req/s. O throughput
medido foi 1.962 RPS (2,5× o de 1 worker) e a latência caiu ~80 %. O ganho não foi 4× porque, a partir de
~2.000 RPS, o gargalo passa a ser o Flask (gunicorn, GIL do Python e a biblioteca `requests` abrindo uma
conexão nova por chamada) — ver seção 4.

---

## 4. Extra: 8 e 16 workers (só possível fora do Windows do Vitor)

| Cenário | Workers | Total req | RPS | Falhas | Média | Mediana | P95 |
|---|---|---|---|---|---|---|---|
| Flask → FastAPI | 8 | 239.316 | 1.988 | 0 | 1.755 ms | 1.600 ms | 2.700 ms |
| Flask → FastAPI | 16 | 240.447 | 1.997 | 1.361 (0,6 %) | 1.725 ms | 1.500 ms | 2.700 ms |
| **Direto na FastAPI** (sem Flask), 90 s | 16 | 391.161 | **4.325** | 0 | **63 ms** | **57 ms** | **95 ms** |

8 e 16 workers ficam travados em ~2.000 RPS: adicionar workers não ajuda mais. Batendo direto na FastAPI com
16 workers, o mesmo Locust e os mesmos 10.000 usuários chegam a 4.325 RPS com mediana de 57 ms — isso
prova que o limite de 2.000 RPS é do Flask, não da FastAPI nem do Locust. Ou seja: escalar workers
resolve o gargalo da calculadora, e aí o próximo gargalo vira o serviço da frente (que precisaria de
mais processos gunicorn, `requests.Session` com pool de conexões, ou um cliente assíncrono).

Sugestão de texto para o relatório: "O uso de múltiplos workers permitiu à FastAPI passar de ~800 para
~3.200 req/s de capacidade. Na prática o sistema completo estabilizou em ~2.000 req/s a partir de 4
workers, porque o gargalo migrou para a aplicação Flask. Isso ilustra que escalar um microserviço isolado
só ajuda até o próximo componente da cadeia saturar."

---

## 5. Passo a passo para reproduzir

### Linux (esta máquina)
```bash
cd radar-enem
python3 -m venv .venv && .venv/bin/pip install fastapi uvicorn pydantic locust
docker compose up --build -d          # Flask (gunicorn) + Locust UI em http://localhost:8089
./fastapi.sh 1                        # FastAPI no host com 1 worker
./rodar_teste.sh 1worker              # 10k usuários, 2 min, CSV em resultados/
./fastapi.sh 4
./rodar_teste.sh 4workers
python3 resumo.py resultados/1worker
python3 resumo.py resultados/4workers
```

### Windows (Vitor) — passo a passo manual
1. Instalar Docker Desktop e Python 3.12+.
2. Na pasta do projeto: `python -m venv .venv`, `.venv\Scripts\activate`, `pip install fastapi uvicorn pydantic`.
3. Terminal 1 — FastAPI: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1`
4. Terminal 2 — Docker: `docker compose up --build` (sobe Flask e Locust).
5. Testar: `curl -X POST http://localhost:5000/exibir_nota -H "Content-Type: application/json" -d "{\"notas\":[720.5,680.0,810.2,640.8,780.0]}"` → deve responder `Sua nota de corte é: 726.3`.
6. Abrir http://localhost:8089 → Number of users **10000**, Spawn rate **500**, Host **http://web_app:5000** → Start. Deixar ~2 min, anotar a tabela (Statistics + Download Data → CSV).
7. Parar o uvicorn (Ctrl+C), subir com `--workers 4`, repetir o passo 6.
8. Observação: no Windows, 10.000 usuários num único processo do Locust vai limitar o Locust em CPU (o
   `--processes` só funciona em Linux/Mac). Se o Locust não chegar em 10k usuários ou a CPU do host ficar em 100 %,
   os números do Windows serão menores que os desta máquina — normal, é o que a seção "Análise" do relatório já avisa.
   Alternativa: rodar `docker compose up --scale locust_tester=...` não resolve; melhor usar modo master/worker do Locust.

---

## 6. Problemas no texto do relatório

1. **Numeração das seções:** vai 5 → 8 → 6 → 7 → 8 → 9. Há dois "8". Renumerar: Docker Compose deveria ser 6, Teste da aplicação 7, Teste de carga 8, 1 worker 9, 4 workers 10.
2. **Título fala em "PaaS, FaaS"**, mas o relatório não menciona FaaS em nenhum lugar. Ou tirar do título ou adicionar um parágrafo relacionando (ex.: a calculadora FastAPI é o candidato natural a virar uma função serverless; o escalonamento por workers que fizemos manualmente é o que um FaaS faz automaticamente).
3. **Locustfile no código ≠ locustfile no relatório.** O do repositório batia em `/api/CalculaNota`; o do relatório em `/exibir_nota`. Já corrigido no repositório.
4. **Seção 6 tem três lugares "A aplicação retornou:" / "foi enviada uma lista" / "O resultado foi:" vazios** — faltam os prints/valores. Valores para preencher: `/` retorna `{"disciplina":"Computacao em Nuvem","projeto":"Radar ENEM","status":"online"}`; entrada `[720.5, 680.0, 810.2, 640.8, 780.0]`; resultado `{"mensagem": "Sua nota de corte é: 726.3"}`.
5. **Dockerfile no relatório usa `CMD ["python", "app.py"]`.** Se o grupo adotar o gunicorn (recomendado — sem isso o teste com 10k usuários não mede os workers, seção 2), atualizar a seção 5 e o `requirements.txt`. Se preferir manter o dev server, reportar os resultados da seção 2 e explicar que o gargalo foi o Flask.
6. **Seção 2 diz que o `host.docker.internal` "permite que o container acesse a API no host".** Verdade no Docker Desktop (Windows/Mac). Em Linux precisa do `extra_hosts` — vale uma nota.
7. **`requirements.txt` instala `fastapi`, `uvicorn` e `locust` dentro da imagem do Flask** sem necessidade (a imagem só roda `app.py`). Não quebra nada, só engorda a imagem. Opcional separar.
8. **Variável `PORT=5000` no compose não é lida** por `app.py` (porta está fixa no `app.run`). Inofensivo; pode remover ou usar `os.getenv("PORT")`.
9. Detalhe de precisão na seção 3: o endpoint é `def` (síncrono), então o `time.sleep(0.05)` roda no threadpool do Starlette (40 threads por worker). É isso que dá o teto de ~800 req/s por worker medido na seção 3.1 — vale citar, explica o número.
