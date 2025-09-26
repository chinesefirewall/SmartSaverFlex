# advisor.py
import os
import json
from typing import List, Dict
from calculator import simulate_flex, simulate_locked, simulate_main, TopUp, Withdrawal

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_OPENAI = bool(OPENAI_API_KEY)

if USE_OPENAI:
    from openai import OpenAI
    client = OpenAI()

with open("truth.json") as f:
    TRUTH = json.load(f)

SYSTEM_PROMPT = """
You are SmartSaver Advisor for Creditstar/Monefit.
Use the TRUTH config below. Do NOT invent rates/terms.
Ask up to 5 onboarding questions (amount, frequency, liquidity, withdrawal estimate, goal),
then recommend Locked Vault / Flex Vault / Main Account, and simulate results (illustrative only).
TRUTH:
{truth}
""".strip()

def _simulate(product: str, initial: float, term_months: int,
              topups=None, withdrawals=None):
    """
    Wrapper to call the right simulation based on product type.
    :param product:
    :param initial:
    :param term_months:
    :param topups:
    :param withdrawals:
    :return:
    Dict with final_balance, interest_accrued, schedule
    """
    topups = topups or []
    withdrawals = withdrawals or []
    if product == "flex":
        return simulate_flex(
            initial, term_months, TRUTH["products"]["flex_vault_apr"],
            [TopUp(**t) for t in topups],
            [Withdrawal(**w) for w in withdrawals]
        )
    if product == "locked":
        return simulate_locked(initial, term_months, TRUTH["products"]["locked_vault_apr"])
    return simulate_main(initial, term_months, TRUTH["products"]["main_account_apr"])

def _fallback_reply(user_msg: str) -> str:
    """
    Lightweight scripted flow so the demo never blocks.
    Tries to find an amount in the user text; otherwise asks for one.
    Args:
        user_msg: str
    Returns: str
    """
    import re
    nums = re.findall(r"\d[\d,\.]*", user_msg.replace("€",""))
    if not nums:
        return ("Let's set up your plan. How much would you like to invest initially? "
                "(e.g., 5000) — illustrative only.")

    initial = float(nums[0].replace(",", ""))
    term = TRUTH["terms"]["min_months"]
    # illustrate flex with one withdrawal example
    sim_flex_break = _simulate("flex", initial, term, withdrawals=[{"month": 6, "amount": min(2000, max(0, initial*0.4))}])
    sim_locked = _simulate("locked", initial, term)
    return (
        f"Illustrative only.\n\n"
        f"Flex (break once @ m6): interest ≈ €{sim_flex_break['interest_accrued']}\n"
        f"Locked ({term}m): interest ≈ €{sim_locked['interest_accrued']}\n\n"
        f"If you'd like, tell me a withdrawal amount and month, e.g. 'withdraw 1500 in month 8'."
    )

def chat(user_msg: str, history: List[Dict[str, str]] | None = None):
    """
    Main chat function to handle user messages and maintain history.
    Uses OpenAI API if key is set; otherwise falls back to scripted responses.
    Args:
        user_msg: str - the latest user message
        history: List of previous messages (dicts with 'role' and 'content')
    Returns:
        assistant_msg: dict with 'role' and 'content'
        updated_history: list including the new user and assistant messages
    """
    history = history or []

    # If no key, use fallback instead of blocking the demo.
    if not USE_OPENAI:
        content = _fallback_reply(user_msg)
        assistant_msg = {"role": "assistant", "content": content}
        updated = history + [{"role": "user", "content": user_msg}, assistant_msg]
        return assistant_msg, updated

    tools = [{
        "type": "function",
        "function": {
            "name": "simulate_returns",
            "description": "Simulate returns for flex, locked, or main",
            "parameters": {
                "type": "object",
                "properties": {
                    "product": {"type": "string", "enum": ["flex","locked","main"]},
                    "initial": {"type": "number"},
                    "term_months": {"type": "integer"},
                    "topups": {"type": "array","items":{"type":"object","properties":{"month":{"type":"integer"},"amount":{"type":"number"}}}},
                    "withdrawals": {"type": "array","items":{"type":"object","properties":{"month":{"type":"integer"},"amount":{"type":"number"}}}}
                },
                "required": ["product","initial","term_months"]
            }
        }
    }]

    sys = {"role": "system", "content": SYSTEM_PROMPT.format(truth=json.dumps(TRUTH, indent=2))}
    msgs = [sys] + history + [{"role": "user", "content": user_msg}]
    resp = client.chat.completions.create(model="gpt-4o-mini", messages=msgs, tools=tools, tool_choice="auto")
    msg = resp.choices[0].message

    if msg.tool_calls:
        call = msg.tool_calls[0]
        if call.function.name == "simulate_returns":
            args = json.loads(call.function.arguments)
            result = _simulate(args["product"], args["initial"], args["term_months"],
                               args.get("topups"), args.get("withdrawals"))
            msgs.append({"role": "assistant", "content": None, "tool_calls": msg.tool_calls})
            msgs.append({"role": "tool", "tool_call_id": call.id, "name": "simulate_returns", "content": json.dumps(result)})
            resp2 = client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
            final = resp2.choices[0].message
            assistant_msg = {"role": "assistant", "content": final.content}
            updated = history + [{"role": "user", "content": user_msg}, assistant_msg]
            return assistant_msg, updated

    assistant_msg = {"role": "assistant", "content": msg.content}
    updated = history + [{"role": "user", "content": user_msg}, assistant_msg]
    return assistant_msg, updated
