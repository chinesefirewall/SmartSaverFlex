# calculator.py
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class TopUp:
    month: int   # 0-based month when the top-up occurs
    amount: float

@dataclass
class Withdrawal:
    month: int
    amount: float

def monthly_interest(amount: float, apr: float) -> float:
    return amount * (apr/100.0) / 12.0

def simulate_flex(initial: float, term_months: int, apr: float, topups: List[TopUp] = None, withdrawals: List[Withdrawal] = None,) -> Dict:
    """ Simulate a flex vault with monthly accrual, top-ups, and withdrawals.
    Args:
        initial: initial amount deposited
        term_months: total term in months to simulate
        apr: annual percentage rate (e.g. 5.0 for 5%)
        topups: list of TopUp instances
        withdrawals: list of Withdrawal instances
    Returns:
        Dict with final_balance, interest_accrued, schedule (list of month, balance, interest)
    """
    topups = topups or []
    withdrawals = withdrawals or []
    # track “chunks” by month added
    chunks = {0: initial}
    for t in topups:
        chunks[t.month] = chunks.get(t.month, 0) + t.amount

    # simulate month by month with simple accrual
    accrued = 0.0
    balance = initial
    schedule = []
    for m in range(term_months):
        # apply withdrawals first in month m
        for w in [w for w in withdrawals if w.month == m]:
            withdraw_amt = min(w.amount, balance)
            balance -= withdraw_amt
            # remove proportionally from chunks
            remaining = withdraw_amt
            for cm in sorted(chunks.keys()):
                if remaining <= 0: break
                take = min(chunks[cm], remaining)
                chunks[cm] -= take
                remaining -= take
        # apply top-ups at month m (already in chunks dict)
        balance = sum([amt for amt in chunks.values()])

        # interest this month across all active chunks
        month_int = 0.0
        for cm, amt in chunks.items():
            if cm <= m and amt > 0:
                month_int += monthly_interest(amt, apr)
        accrued += month_int
        schedule.append({"month": m+1, "balance": round(balance,2), "interest": round(month_int,2)})

    return {
        "final_balance": round(balance, 2),
        "interest_accrued": round(accrued, 2),
        "schedule": schedule
    }

def simulate_locked(initial: float, term_months: int, apr: float) -> Dict:
    # simple monthly accrual, no early withdrawals, no top-ups
    monthly = monthly_interest(initial, apr)
    accrued = monthly * term_months
    return {
        "final_balance": round(initial, 2),
        "interest_accrued": round(accrued, 2)
    }

def simulate_main(initial: float, term_months: int, apr: float) -> Dict:
    monthly = monthly_interest(initial, apr)
    accrued = monthly * term_months
    return {
        "final_balance": round(initial, 2),
        "interest_accrued": round(accrued, 2)
    }
