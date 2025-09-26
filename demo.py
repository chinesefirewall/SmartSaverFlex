# demo.py
import streamlit as st
import requests
import json
import pandas as pd
from advisor import chat

# Load custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("styles.css")

st.set_page_config(page_title="SmartSaver Flex Vault Demo", layout="wide")

# Add "monefit" title at the top left
st.markdown("""
<div style="padding: 1rem 2rem; text-align: left; background: #f9f6f4;">
    <h2 style="font-size: 1.8rem; font-weight: 700; margin: 0;">monefit</h2>
</div>
""", unsafe_allow_html=True)

# Hero / headline block
st.markdown("""
<div style="padding: 3rem; text-align: center; background: #e6f5e6; border-radius: 20px; margin-bottom: 2rem;">
    <h1 style="font-size: 2.5rem;">Daily returns up to <span style="color:#0d7d0d;">10.52% APY</span></h1>
    <p style="font-size: 1.2rem; color: #333;">Trusted by investors in over 32 countries, €8 million earned already.</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Truth Config
st.sidebar.header("Vault Truth Config")
with open("truth.json") as f:
    truth = json.load(f)
st.sidebar.json(truth)

# Layout
col1, col2 = st.columns(2)

# --- Left: Chat Advisor ---
with col1:
    st.subheader("🤖  Advisor Chat")


    QUESTIONS = [
        {
            "key": "goal",
            "prompt": (
                "What’s your main goal for this vault? 🤔\n"
                "Are you saving for something specific like an apartment or wedding, "
                "want to grow your portfolio, or just earn steady passive income?"
            ),
            "type": "goal"
        },
        {
            "key": "initial",
            "prompt": (
                "Great! Do you already have an amount in mind that you’d like to invest straight away? 💶 "
                "(e.g., 1000, 5000)"
            ),
            "type": "float"
        },
        {
            "key": "frequency",
            "prompt": (
                "Do you plan to top up your savings regularly, or would this just be a one-time deposit? 📅\n"
                "If regularly, how often (monthly, quarterly, etc.) and roughly how much?"
            ),
            "type": "str"
        },
        {
            "key": "liquidity",
            "prompt": (
                "How important is flexibility to you? 🔑\n"
                "Do you want the option to take money out once during the term if needed? (yes/no)"
            ),
            "type": "bool"
        },
        {
            "key": "withdraw",
            "prompt": (
                "If you think you might withdraw, do you know how much and around when? "
                "(e.g., '2000 in month 6' or just type 'none' if not sure)"
            ),
            "type": "withdraw"
        },
        {
            "key": "term",
            "prompt": (
                "And finally, how long do you want to keep the money invested? ⏳\n"
                "You can choose anywhere between 12 and 24 months (e.g., 12, 18, 24)."
            ),
            "type": "term"
        }
    ]


    def init_qa():
        st.session_state.qa = {
            "step": 0,
            "answers": {
                "initial": None,
                "term": None,
                "frequency": None,
                "liquidity": None,
                "withdraw_amount": None,
                "withdraw_month": None,
                "goal": None,
            },
            "history": []
        }

    if "qa" not in st.session_state:
        init_qa()

    def current_prompt():
        step = st.session_state.qa["step"]
        if step < len(QUESTIONS):
            return QUESTIONS[step]["prompt"]
        return "You're all set. Type 'restart' to try another scenario."

    # ---------- Parsers ----------
    import re
    def parse_float(text):
        try:
            return float(text.replace("€", "").replace(",", "").strip())
        except Exception:
            return None

    def parse_term(text):
        # Expect integer 12..24
        try:
            val = int(float(text.strip()))
            if 12 <= val <= 24:
                return val
            return None
        except Exception:
            return None

    def parse_bool(text):
        t = text.strip().lower()
        if t in ["yes", "y", "true", "1"]: return True
        if t in ["no", "n", "false", "0"]: return False
        return None

    def parse_withdraw(text):
        t = text.strip().lower()
        if t in ["none", "no", "n", "0", "skip"]:
            return None, None
        nums = re.findall(r"\d[\d,\.]*", t)
        amt = None
        mon = None
        if nums:
            amt = parse_float(nums[0])
            if len(nums) >= 2:
                try:
                    mon = int(float(nums[1]))
                except Exception:
                    mon = None
        return amt, mon

    def parse_goal(text: str):
        t = text.strip().lower()

        # Direct intent keywords
        if any(x in t for x in ["apartment", "house", "wedding", "holiday", "car"]):
            return "short_term_goal"
        if any(x in t for x in ["grow", "portfolio", "long term", "retirement", "wealth"]):
            return "long_term_growth"
        if any(x in t for x in ["passive", "income", "side hustle"]):
            return "passive_income"
        if any(x in t for x in ["safe", "safety", "flexibility", "liquid", "access"]):
            return "flexibility_with_safety"
        if any(x in t for x in ["max", "maximum", "returns", "yield"]):
            return "maximum_returns"

        # Fallback → assume flexibility if unsure
        return "flexibility_with_safety"

    # ---------- Simple recommender ----------
    def recommend_product(a: dict) -> str:
        if a["liquidity"] or a["withdraw_amount"]:
            return "flex"
        if a["goal"] in ["maximum_returns", "long_term_growth"]:
            return "locked"
        if a["goal"] in ["short_term_goal", "passive_income", "flexibility_with_safety"]:
            return "flex"
        return "main"

    # ---------- Simulations via your FastAPI ----------
    def simulate_all(a: dict) -> dict:
        base = "http://127.0.0.1:8000"
        # Locked
        locked = requests.post(f"{base}/simulate/locked", json={
            "initial": a["initial"], "term_months": a["term"]
        }).json()
        # Main
        main = requests.post(f"{base}/simulate/main", json={
            "initial": a["initial"], "term_months": a["term"]
        }).json()
        # Flex (with optional withdrawal)
        w = []
        if a["withdraw_amount"] and a["withdraw_month"] is not None:
            w = [{"month": int(a["withdraw_month"]), "amount": float(a["withdraw_amount"])}]
        flex = requests.post(f"{base}/simulate/flex", json={
            "initial": a["initial"], "term_months": a["term"], "withdrawals": w
        }).json()
        return {"locked": locked, "main": main, "flex": flex}

    # Show compact history
    for entry in st.session_state.qa["history"]:
        st.markdown(f"**{entry['role']}:** {entry['text']}")

    # Guided chat input (nudging placeholder)
    user_text = st.chat_input(placeholder=f"{current_prompt()}")

    if user_text:
        if user_text.strip().lower() == "restart":
            init_qa()
            st.rerun()

        st.session_state.qa["history"].append({"role": "You", "text": user_text})
        step = st.session_state.qa["step"]

        if step < len(QUESTIONS):
            q = QUESTIONS[step]
            typ = q["type"]
            ok, err = True, None

            if typ == "float":
                val = parse_float(user_text)
                if val is None or val <= 0:
                    ok, err = False, "Please enter a positive number like 5000."
                else:
                    st.session_state.qa["answers"]["initial"] = val

            elif typ == "term":
                t = parse_term(user_text)
                if t is None:
                    ok, err = False, "Please enter an integer between 12 and 24 (e.g., 12 or 18)."
                else:
                    st.session_state.qa["answers"]["term"] = t

            elif typ == "str":
                st.session_state.qa["answers"]["frequency"] = user_text.strip()

            elif typ == "bool":
                b = parse_bool(user_text)
                if b is None:
                    ok, err = False, "Please answer yes or no."
                else:
                    st.session_state.qa["answers"]["liquidity"] = b

            elif typ == "withdraw":
                amt, mon = parse_withdraw(user_text)
                st.session_state.qa["answers"]["withdraw_amount"] = amt
                st.session_state.qa["answers"]["withdraw_month"] = mon

            elif typ == "goal":
                g = parse_goal(user_text)
                st.session_state.qa["answers"]["goal"] = g

            if not ok:
                st.session_state.qa["history"].append({"role": "Advisor", "text": err})
            else:
                st.session_state.qa["step"] += 1
                if st.session_state.qa["step"] < len(QUESTIONS):
                    st.session_state.qa["history"].append({"role": "Advisor", "text": current_prompt()})
                else:
                    # --------- FINALIZE: recommend + simulate ----------
                    a = st.session_state.qa["answers"]
                    try:
                        sims = simulate_all(a)
                        rec = recommend_product(a)
                        # Format output
                        def eur(x): 
                            try: return f"€{float(x):,.0f}"
                            except: return str(x)

                        # Convert goal category to human-readable text
                        def goal_text(goal):
                            if goal == "short_term_goal":
                                return "Short-term savings goal"
                            elif goal == "long_term_growth":
                                return "Long-term portfolio growth"
                            elif goal == "passive_income":
                                return "Steady passive income"
                            elif goal == "flexibility_with_safety":
                                return "Flexibility with safety"
                            elif goal == "maximum_returns":
                                return "Maximum returns"
                            else:
                                return goal

                        # Simulated interest figures
                        locked_i  = eur(sims["locked"]["interest_accrued"])
                        classic_i = eur(sims["main"]["interest_accrued"])   # Main -> SmartSaver Classic
                        flex_i    = eur(sims["flex"]["interest_accrued"])   # Flex -> SmartSaver Flex Premium

                        withdraw_text = (
                            f"€{int(a['withdraw_amount'])} at month {a['withdraw_month']}"
                            if a["withdraw_amount"] else "none"
                        )

                        # Map internal product codes to display names
                        rec_labels = {
                            "locked": "Locked Vault",
                            "main": "SmartSaver Classic",
                            "flex": "SmartSaver Flex Premium",
                        }
                        rec_label = rec_labels.get(rec, rec.title())

                        summary = (
                            "Illustrative only.\n\n"
                            f"**Your plan summary**\n"
                            f"- Initial: **{eur(a['initial'])}**\n"
                            f"- Term: **{a['term']} months**\n"
                            f"- Frequency: **{a['frequency']}**\n"
                            f"- Liquidity option: **{'yes' if a['liquidity'] else 'no'}**\n"
                            f"- Withdrawal: **{withdraw_text}**\n"
                            f"- Goal: **{goal_text(a['goal'])}**\n\n"
                            f"**Simulated outcomes**\n"
                            f"- Locked Vault: interest ≈ **{locked_i}**\n"
                            f"- SmartSaver Flex Premium: interest ≈ **{flex_i}** "
                            f"{'(with one break)' if a['withdraw_amount'] else '(no break)'}\n"
                            f"- SmartSaver Classic: interest ≈ **{classic_i}**\n\n"
                            f"**Recommendation:** **{rec_label}** "
                            f"(based on your liquidity need and goal). "
                            f"Click **Apply answers to calculator** or tweak values on the right."
                        )

                        st.session_state.qa["history"].append({"role": "Advisor", "text": summary})
                        st.session_state.qa["complete"] = True
                        st.session_state.qa["final_answers"] = a
                    except Exception as e:
                        st.session_state.qa["history"].append({"role": "Advisor", "text": f"Could not run simulation: {e}"})

        st.rerun()

    # --- Show "Apply answers" button when interview is complete ---
    if st.session_state.qa.get("complete"):
        st.markdown("**Recommendation ready.** You can apply these answers to the calculator on the right.")
        if st.button("Apply answers to calculator", type="primary", use_container_width=True, key="apply_to_calc"):
            a = st.session_state.qa.get("final_answers", {})
            try:
                st.session_state["calc_initial"] = int(a.get("initial") or 0)
                st.session_state["calc_term"] = int(a.get("term") or 12)
                st.session_state["calc_withdraw_month"] = int(a.get("withdraw_month") or 0)
                st.session_state["calc_withdraw_amt"] = int(a.get("withdraw_amount") or 0)
                st.session_state["calc_applied"] = True
                st.toast("Applied to calculator ✓", icon="✅")
                st.session_state["auto_run_sim"] = True  # Flag to auto-run simulation
            except Exception:
                st.session_state["calc_applied"] = False
            st.rerun()

    # Progress chip (optional)
    st.caption(f"Step {min(st.session_state.qa['step']+1, len(QUESTIONS))} of {len(QUESTIONS)} • Type 'restart' to start over")

# --- Right: Break Calculator ---
with col2:
    st.subheader("Investment Calculator")

    # Sensible defaults if chat hasn't filled them yet
    st.session_state.setdefault("calc_initial", 5000)
    st.session_state.setdefault("calc_term", 12)
    st.session_state.setdefault("calc_withdraw_month", 6)
    st.session_state.setdefault("calc_withdraw_amt", 2000)

    # Widgets bound to session keys so we can update them from the chat
    initial = st.number_input(
        "Initial Investment (€)",
        min_value=1000, max_value=100000, step=500,
        value=st.session_state["calc_initial"],
        key="calc_initial"
    )

    term = st.slider(
        "Vault Term (months)",
        min_value=12, max_value=24,
        value=int(st.session_state["calc_term"]),
        key="calc_term"
    )

    # Keep withdraw month within current term range
    wm_default = min(int(st.session_state["calc_withdraw_month"]), int(term))
    withdraw_month = st.slider(
        "Withdrawal Month",
        min_value=0, max_value=int(term),
        value=wm_default,
        key="calc_withdraw_month"
    )

    withdraw_amt = st.number_input(
        "Withdrawal Amount (€)",
        min_value=0, max_value=int(initial), step=500,
        value=int(st.session_state["calc_withdraw_amt"]),
        key="calc_withdraw_amt"
    )

    # Auto-run simulation if flag is set
    auto_run = st.session_state.get("auto_run_sim", False)
    if auto_run:
        st.session_state["auto_run_sim"] = False  # Reset flag
        run_sim = True
    else:
        run_sim = st.button("Run Simulation", use_container_width=True)

    if run_sim:
        url = "http://127.0.0.1:8000/simulate/flex"
        payload = {
            "initial": initial,
            "term_months": term,
            "withdrawals": [{"month": withdraw_month, "amount": withdraw_amt}]
        }
        resp = requests.post(url, json=payload)
        data = resp.json()

        st.success("Simulation Complete")
        st.json(data)

        # NEW CHART BLOCK (pandas-based)
        # The API returns 'schedule' as a list of dicts; sometimes it may be a dict keyed by ints.
        schedule = data.get("schedule", [])

        # If schedule is a dict (0: {...}, 1: {...}), normalize it to a list of rows.
        if isinstance(schedule, dict):
            schedule = list(schedule.values())

        # Build a DataFrame
        df = pd.DataFrame(schedule)  # columns: month, balance, interest

        # Safety: ensure expected columns exist
        expected_cols = {"month", "balance", "interest"}
        missing = expected_cols - set(df.columns)
        if missing:
            st.warning(f"Schedule missing columns: {missing}")
        else:
            # Use 'month' as x-axis and 'balance' as y-axis
            st.subheader("Balance Over Time")
            st.line_chart(df, x="month", y="balance")

            # Optional: also plot monthly interest
            st.subheader("Monthly Interest Accrued")
            st.line_chart(df, x="month", y="interest")

