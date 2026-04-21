# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 11:16:41 2026

@author: Saeed.Janani
"""

import math
import random
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import streamlit as st


# ============================================================
# Page setup
# ============================================================
st.set_page_config(
    page_title="Pricing Simulation Pilot V2",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Styling
# ============================================================
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.25rem;
            padding-bottom: 2rem;
            max-width: 1350px;
        }
        .hero {
            padding: 1.2rem 1.4rem;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(37,99,235,.16), rgba(16,185,129,.12));
            border: 1px solid rgba(255,255,255,.08);
            margin-bottom: 1rem;
        }
        .card {
            background: rgba(255,255,255,.03);
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 16px;
            padding: 1rem;
            margin-bottom: .9rem;
        }
        .card-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: .45rem;
        }
        .pill {
            display: inline-block;
            padding: .25rem .65rem;
            margin: .18rem .35rem .18rem 0;
            border-radius: 999px;
            background: rgba(59,130,246,.12);
            border: 1px solid rgba(59,130,246,.25);
            font-size: .85rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,.03);
            border: 1px solid rgba(255,255,255,.08);
            padding: .75rem .9rem;
            border-radius: 14px;
        }
        div[data-testid="stForm"] {
            background: rgba(255,255,255,.03);
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 16px;
            padding: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Model definitions
# ============================================================
MARKETS = ["A", "B", "C", "D"]
TOTAL_ROUNDS = 5
OUR_QUALITY = 1.00
C1_QUALITY = 0.95
C2_QUALITY = 1.03
NOISE_BOUND = 0.10

OWN_PRICE_WEIGHT = 5
COMP_PRICE_WEIGHT = 3
QUALITY_WEIGHT = 2
TOTAL_WEIGHT = OWN_PRICE_WEIGHT + COMP_PRICE_WEIGHT + QUALITY_WEIGHT

BASE_MARKET_DEMAND = {
    "A": 1000,
    "B": 1200,
    "C": 1000,
    "D": 1300,
}

OWN_PRICE_SENSITIVITY = {
    "A": 5,
    "B": 7,
    "C": 8,
    "D": 9,
}

COMP_PRICE_SENSITIVITY = {
    "A": 6,
    "B": 7,
    "C": 5,
    "D": 4,
}

EXTRA_LOGISTICS_COST = {
    "A": 0,
    "B": 1,
    "C": 1,
    "D": 2,
}

COMPETITOR_COVERAGE = {
    "A": ["C1"],
    "B": ["C1"],
    "C": ["C2"],
    "D": ["C2"],
}

BASE_PRICE_TEMPLATE = {
    "ours": {"A": 40, "B": 41, "C": 42, "D": 43},
    "C1": {"A": 39, "B": 40},
    "C2": {"C": 43, "D": 44},
}


@dataclass(frozen=True)
class RoundScenario:
    round_no: int
    title: str
    c1_discount_pct: float = 0.0
    c2_discount_pct: float = 0.0


ROUND_SCENARIOS: List[RoundScenario] = [
    RoundScenario(1, "Baseline competition"),
    RoundScenario(2, "Stable market"),
    RoundScenario(3, "Competitor 1 discount shock", c1_discount_pct=0.30),
    RoundScenario(4, "Competitor 2 discount shock", c2_discount_pct=0.15),
    RoundScenario(5, "Post-promotion normalization"),
]


# ============================================================
# Cost and demand logic
# ============================================================
def manufacturing_unit_cost(total_units: float) -> float:
    if total_units > 3000:
        return 20.0
    if total_units > 1000:
        return 23.0
    return 25.0


def market_competitor_price(market: str, scenario: RoundScenario) -> float:
    if "C1" in COMPETITOR_COVERAGE[market]:
        base_price = BASE_PRICE_TEMPLATE["C1"][market]
        return round(base_price * (1 - scenario.c1_discount_pct), 2)
    if "C2" in COMPETITOR_COVERAGE[market]:
        base_price = BASE_PRICE_TEMPLATE["C2"][market]
        return round(base_price * (1 - scenario.c2_discount_pct), 2)
    raise ValueError(f"No competitor configured for market {market}")


def market_competitor_quality(market: str) -> float:
    return C1_QUALITY if "C1" in COMPETITOR_COVERAGE[market] else C2_QUALITY


def base_demand_per_firm(market: str) -> float:
    num_competitors = 1 + len(COMPETITOR_COVERAGE[market])
    return BASE_MARKET_DEMAND[market] / num_competitors


def quality_factor(our_quality: float, competitor_quality: float) -> float:
    ratio = max(our_quality / competitor_quality, 0.01)
    return ratio ** (QUALITY_WEIGHT / TOTAL_WEIGHT)


def price_factor(our_price: float, competitor_price: float, market: str) -> float:
    own_component = max(our_price, 1.0) ** (-OWN_PRICE_WEIGHT * OWN_PRICE_SENSITIVITY[market] / TOTAL_WEIGHT)
    competitor_component = max(competitor_price, 1.0) ** (COMP_PRICE_WEIGHT * COMP_PRICE_SENSITIVITY[market] / TOTAL_WEIGHT)
    return own_component * competitor_component


def compute_market_quantity(
    market: str,
    our_price: float,
    scenario: RoundScenario,
    our_quality: float = OUR_QUALITY,
    rng: random.Random | None = None,
) -> Dict[str, float | str]:
    competitor_price = market_competitor_price(market, scenario)
    competitor_quality = market_competitor_quality(market)
    base_demand = base_demand_per_firm(market)

    deterministic_quantity = (
        base_demand
        * price_factor(our_price, competitor_price, market)
        * quality_factor(our_quality, competitor_quality)
    )

    if rng is None:
        rng = random.Random()
    noise_multiplier = rng.uniform(1 - NOISE_BOUND, 1 + NOISE_BOUND)
    quantity = max(deterministic_quantity * noise_multiplier, 0.0)

    return {
        "market": market,
        "base_demand": round(base_demand, 2),
        "market_size": float(BASE_MARKET_DEMAND[market]),
        "our_price": round(our_price, 2),
        "competitor_price": round(competitor_price, 2),
        "our_quality": round(our_quality, 3),
        "competitor_quality": round(competitor_quality, 3),
        "noise_multiplier": round(noise_multiplier, 4),
        "quantity": round(quantity, 2),
    }


def compute_round_results(
    prices: Dict[str, float],
    scenario: RoundScenario,
    rng_seed: int,
) -> Dict[str, object]:
    rng = random.Random(rng_seed)
    market_results: List[Dict[str, float | str]] = []

    for market in MARKETS:
        market_results.append(
            compute_market_quantity(
                market=market,
                our_price=float(prices[market]),
                scenario=scenario,
                rng=rng,
            )
        )

    total_units = sum(float(row["quantity"]) for row in market_results)
    base_uvc = manufacturing_unit_cost(total_units)

    total_revenue = 0.0
    total_variable_cost = 0.0
    total_profit = 0.0

    for row in market_results:
        market = str(row["market"])
        quantity = float(row["quantity"])
        price = float(row["our_price"])
        uvc = base_uvc + EXTRA_LOGISTICS_COST[market]
        revenue = price * quantity
        variable_cost = uvc * quantity
        profit = revenue - variable_cost

        row["uvc"] = round(uvc, 2)
        row["revenue"] = round(revenue, 2)
        row["variable_cost"] = round(variable_cost, 2)
        row["profit"] = round(profit, 2)

        total_revenue += revenue
        total_variable_cost += variable_cost
        total_profit += profit

    return {
        "round_no": scenario.round_no,
        "title": scenario.title,
        "base_uvc": round(base_uvc, 2),
        "total_units": round(total_units, 2),
        "total_revenue": round(total_revenue, 2),
        "total_variable_cost": round(total_variable_cost, 2),
        "total_profit": round(total_profit, 2),
        "markets": market_results,
    }


def summarize_history(history: List[Dict[str, object]]) -> Dict[str, float]:
    if not history:
        return {
            "cumulative_profit": 0.0,
            "cumulative_revenue": 0.0,
            "cumulative_units": 0.0,
            "avg_profit_per_round": 0.0,
        }

    cumulative_profit = sum(float(row["total_profit"]) for row in history)
    cumulative_revenue = sum(float(row["total_revenue"]) for row in history)
    cumulative_units = sum(float(row["total_units"]) for row in history)

    return {
        "cumulative_profit": round(cumulative_profit, 2),
        "cumulative_revenue": round(cumulative_revenue, 2),
        "cumulative_units": round(cumulative_units, 2),
        "avg_profit_per_round": round(cumulative_profit / len(history), 2),
    }


def market_feedback(round_result: Dict[str, object]) -> str:
    market_rows = round_result["markets"]
    best_market = max(market_rows, key=lambda x: float(x["profit"]))
    worst_market = min(market_rows, key=lambda x: float(x["profit"]))
    return (
        f"Best market this round: {best_market['market']} with profit ${float(best_market['profit']):,.0f}. "
        f"Weakest market: {worst_market['market']} with profit ${float(worst_market['profit']):,.0f}."
    )


# ============================================================
# Session state
# ============================================================
def init_state() -> None:
    if "team_name" not in st.session_state:
        st.session_state.team_name = ""
    if "round_idx" not in st.session_state:
        st.session_state.round_idx = 0
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "noise_seed_base" not in st.session_state:
        st.session_state.noise_seed_base = 2026
    if "default_prices" not in st.session_state:
        st.session_state.default_prices = BASE_PRICE_TEMPLATE["ours"].copy()


init_state()


def reset_simulation() -> None:
    st.session_state.round_idx = 0
    st.session_state.history = []
    st.session_state.last_result = None


# ============================================================
# Sidebar
# ============================================================
st.sidebar.markdown("## ⚙️ Simulation Controls")
st.sidebar.text_input("Team / student name", key="team_name")
st.sidebar.number_input("Noise seed base", min_value=1, max_value=999999, key="noise_seed_base")

st.sidebar.markdown("### Starting price defaults")
for market in MARKETS:
    st.session_state.default_prices[market] = st.sidebar.slider(
        f"Default price for market {market}",
        min_value=20,
        max_value=80,
        value=int(st.session_state.default_prices[market]),
        step=1,
    )

if st.sidebar.button("Restart simulation", use_container_width=True):
    reset_simulation()
    st.rerun()

with st.sidebar.expander("Model assumptions", expanded=False):
    st.write("Demand depends on own price, competitor price, market base demand, and relative product quality.")
    st.write("Random noise is applied up to ±10% in each market each round.")
    st.write("Competitor 1 only operates in A and B. Competitor 2 only operates in C and D.")
    st.write("Round 3 applies a 30% discount to Competitor 1. Round 4 applies a 15% discount to Competitor 2.")
    st.write("Manufacturing cost tier: $25 up to 1000 units, $23 above 1000 and up to 3000, $20 above 3000.")


# ============================================================
# Header and top metrics
# ============================================================
st.markdown(
    """
    <div class="hero">
        <h1>🌍 Multi-Market Pricing Simulation — Pilot V2</h1>
        <p>Five rounds, four markets, asymmetric competition, quality differences, location-specific costs, and controlled noise.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

completed = st.session_state.round_idx >= TOTAL_ROUNDS
summary = summarize_history(st.session_state.history)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Round", f"{min(st.session_state.round_idx + 1, TOTAL_ROUNDS)}/{TOTAL_ROUNDS}" if not completed else f"{TOTAL_ROUNDS}/{TOTAL_ROUNDS}")
m2.metric("Cumulative profit", f"${summary['cumulative_profit']:,.0f}")
m3.metric("Cumulative units", f"{summary['cumulative_units']:,.0f}")
m4.metric("Team", st.session_state.team_name if st.session_state.team_name else "Not set")


# ============================================================
# Completed view
# ============================================================
if completed:
    st.success("Simulation completed.")
    history_rows = []
    market_rows = []

    for round_result in st.session_state.history:
        history_rows.append({
            "round_no": round_result["round_no"],
            "title": round_result["title"],
            "base_uvc": round_result["base_uvc"],
            "total_units": round_result["total_units"],
            "total_revenue": round_result["total_revenue"],
            "total_profit": round_result["total_profit"],
        })
        for market_result in round_result["markets"]:
            market_rows.append({
                "round_no": round_result["round_no"],
                **market_result,
            })

    rounds_df = pd.DataFrame(history_rows)
    markets_df = pd.DataFrame(market_rows)

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown('<div class="card"><div class="card-title">Round-level performance</div></div>', unsafe_allow_html=True)
        a, b, c = st.columns(3)
        a.metric("Total revenue", f"${summary['cumulative_revenue']:,.0f}")
        b.metric("Average profit / round", f"${summary['avg_profit_per_round']:,.0f}")
        c.metric("Rounds", f"{TOTAL_ROUNDS}")
        st.line_chart(rounds_df.set_index("round_no")[["total_profit", "total_revenue", "total_units"]])

    with right:
        st.markdown('<div class="card"><div class="card-title">Market-level results</div></div>', unsafe_allow_html=True)
        display_df = markets_df[[
            "round_no", "market", "our_price", "competitor_price", "quantity", "uvc", "revenue", "profit"
        ]].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="card"><div class="card-title">Round summary table</div></div>', unsafe_allow_html=True)
    st.dataframe(rounds_df, use_container_width=True, hide_index=True)

    csv = markets_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download detailed market results CSV",
        data=csv,
        file_name="pricing_pilot_v2_market_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.stop()


# ============================================================
# Active round view
# ============================================================
scenario = ROUND_SCENARIOS[st.session_state.round_idx]
left, right = st.columns([1.05, 1], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-title">Round {scenario.round_no}: {scenario.title}</div>', unsafe_allow_html=True)
    st.write("Set your price independently for each market.")

    pill_text = []
    if scenario.c1_discount_pct > 0:
        pill_text.append(f"C1 discount active: {int(scenario.c1_discount_pct * 100)}%")
    if scenario.c2_discount_pct > 0:
        pill_text.append(f"C2 discount active: {int(scenario.c2_discount_pct * 100)}%")
    if not pill_text:
        pill_text.append("No competitor promotion active")

    for txt in pill_text:
        st.markdown(f'<span class="pill">{txt}</span>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("round_form"):
        st.markdown("#### Your prices by market")
        col_a, col_b = st.columns(2)
        with col_a:
            price_a = st.slider("Market A", 20, 80, int(st.session_state.default_prices["A"]), 1)
            price_b = st.slider("Market B", 20, 80, int(st.session_state.default_prices["B"]), 1)
        with col_b:
            price_c = st.slider("Market C", 20, 80, int(st.session_state.default_prices["C"]), 1)
            price_d = st.slider("Market D", 20, 80, int(st.session_state.default_prices["D"]), 1)

        submitted = st.form_submit_button("Submit round", use_container_width=True)

    if submitted:
        price_dict = {"A": price_a, "B": price_b, "C": price_c, "D": price_d}
        round_result = compute_round_results(
            prices=price_dict,
            scenario=scenario,
            rng_seed=st.session_state.noise_seed_base + scenario.round_no,
        )
        st.session_state.last_result = round_result
        st.session_state.history.append(round_result)
        st.session_state.round_idx += 1
        st.rerun()

with right:
    st.markdown('<div class="card"><div class="card-title">Market setup this round</div></div>', unsafe_allow_html=True)
    setup_rows = []
    for market in MARKETS:
        setup_rows.append({
            "market": market,
            "market_demand": BASE_MARKET_DEMAND[market],
            "base_demand_per_firm": base_demand_per_firm(market),
            "own_price_sens": OWN_PRICE_SENSITIVITY[market],
            "comp_price_sens": COMP_PRICE_SENSITIVITY[market],
            "extra_cost": EXTRA_LOGISTICS_COST[market],
            "competitor": ", ".join(COMPETITOR_COVERAGE[market]),
            "competitor_price": market_competitor_price(market, scenario),
            "competitor_quality": market_competitor_quality(market),
        })
    setup_df = pd.DataFrame(setup_rows)
    st.dataframe(setup_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="card"><div class="card-title">Latest round result</div></div>', unsafe_allow_html=True)
    if st.session_state.last_result is None:
        st.info("Submit the first round to see performance details.")
    else:
        latest = st.session_state.last_result
        r1, r2, r3 = st.columns(3)
        r1.metric("Round profit", f"${float(latest['total_profit']):,.0f}")
        r2.metric("Round units", f"{float(latest['total_units']):,.0f}")
        r3.metric("Base manufacturing UVC", f"${float(latest['base_uvc']):,.0f}")
        st.write(market_feedback(latest))

        latest_df = pd.DataFrame(latest["markets"])
        show_df = latest_df[[
            "market", "our_price", "competitor_price", "quantity", "noise_multiplier", "uvc", "revenue", "profit"
        ]].copy()
        st.dataframe(show_df, use_container_width=True, hide_index=True)

    if st.session_state.history:
        st.markdown('<div class="card"><div class="card-title">Performance trend</div></div>', unsafe_allow_html=True)
        trend_df = pd.DataFrame([
            {
                "round_no": row["round_no"],
                "profit": row["total_profit"],
                "revenue": row["total_revenue"],
                "units": row["total_units"],
            }
            for row in st.session_state.history
        ]).set_index("round_no")
        st.line_chart(trend_df)
