# app.py
import json
from fastapi import FastAPI
from pydantic import BaseModel
from calculator import simulate_flex, simulate_locked, simulate_main, TopUp, Withdrawal

with open("truth.json") as f:
    TRUTH = json.load(f)

app = FastAPI(title="SmartSaver Flex Vault API")

class FlexRequest(BaseModel):
    initial: float
    term_months: int
    topups: list[TopUp] = []
    withdrawals: list[Withdrawal] = []

@app.get("/truth")
def get_truth(): return TRUTH

@app.post("/simulate/flex")
def flex(req: FlexRequest):
    apr = TRUTH["products"]["flex_vault_apr"]
    return simulate_flex(req.initial, req.term_months, apr, req.topups, req.withdrawals)

class SimpleRequest(BaseModel):
    initial: float
    term_months: int

@app.post("/simulate/locked")
def locked(req: SimpleRequest):
    apr = TRUTH["products"]["locked_vault_apr"]
    return simulate_locked(req.initial, req.term_months, apr)

@app.post("/simulate/main")
def main(req: SimpleRequest):
    apr = TRUTH["products"]["main_account_apr"]
    return simulate_main(req.initial, req.term_months, apr)
