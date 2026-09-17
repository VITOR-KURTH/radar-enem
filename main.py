import time
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List


class Notas(BaseModel):
    notas: List[float]


app = FastAPI()


@app.post("/api/CalculaNota")
def calcular(payload: Notas):
    time.sleep(0.05)
    nota_corte = sum(payload.notas) / len(payload.notas)
    return {"nota_corte_calculada": round(nota_corte, 2)}