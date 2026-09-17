FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

# Servidor de produção (gunicorn) no lugar do dev server do Flask:
# 8 processos x 64 threads, keep-alive e backlog maior para aguentar carga.
# Para desenvolvimento local ainda dá para usar: python app.py
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", \
     "--workers", "8", "--threads", "64", "--keep-alive", "5", \
     "--backlog", "4096", "--log-level", "warning"]
