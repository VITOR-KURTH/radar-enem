from locust import HttpUser, task, between
import random


class AlunoRadarEnem(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Escolhe uma porta aleatória entre os 4 servidores
        self.port = random.choice([8000, 8001, 8002, 8003])
        print(f"[USER {self.client_id}] Conectado na porta {self.port}")  # ⭐ LOG

    @task
    def calcular_nota(self):
        payload = {
            "notas": [720.5, 680.0, 810.2, 640.8, 780.0]
        }

        self.client.post(
            f"http://127.0.0.1:{self.port}/api/CalculaNota",
            json=payload
        )