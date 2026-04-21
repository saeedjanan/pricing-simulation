# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 11:16:41 2026

@author: Saeed.Janani
"""

import random
from dataclasses import dataclass, replace
from typing import Dict, List

import pandas as pd
import streamlit as st


# ============================================================
# Page setup
# ============================================================
st.set_page_config(
    page_title="Pricing Simulation — Pilot V2",
    page_icon="📈",
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
            max-width: 1450px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }
        .topbar {
            background: #081b56;
            border-radius: 20px;
            padding: 1.1rem 1.35rem;
            margin-bottom: 1rem;
            color: white;
        }
        .topbar h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.1;
        }
        .topbar p {
            margin: .35rem 0 0 0;
            color: #dbe7ff;
            font-size: 1rem;
        }
        .section-card {
            background: #ffffff;
            border: 1px solid #d8dee9;
            border-radius: 16px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 14px rgba(15,23,42,.05);
        }
        .section-title {
            background: #071f63;
            color: white;
            padding: .75rem 1rem;
            border-radius: 10px;
            font-weight: 700;
            font-size: 1.05rem;
            margin-bottom: .9rem;
        }
        .market-grid-title {
            font-weight: 700;
            font-size: 1.05rem;
            color: #1f2937;
            margin-bottom: .7rem;
        }
        .market-card {
            border-radius: 16px;
            padding: 1rem;
            min-height: 215px;
            border: 2px solid #dbe2ea;
            margin-bottom: .8rem;
        }
        .market-card.active {
            background: #eef7ec;
            border-color: #6db36d;
        }
        .market-card.unlocked {
            background: #f8fbff;
            border-color: #a8c5ff;
        }
        .market-card.locked {
            background: #faf7f4;
            border-color: #ead7c4;
            opacity: .95;
        }
        .market-name {
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1;
            margin-bottom: .35rem;
            text-align: center;
        }
        .market-sub {
            text-align: center;
            color: #374151;
            font-weight: 600;
            margin-bottom: .6rem;
        }
        .market-stat {
            text-align: center;
            margin-top: .35rem;
            color: #111827;
        }
        .market-demand {
            font-size: 2rem;
            font-weight: 800;
            text-align: center;
            margin: .2rem 0;
        }
        .status-bar {
            border-radius: 0 0 12px 12px;
            margin: 1rem -.95rem -.95rem -.95rem;
            padding: .65rem;
            font-weight: 700;
            text-align: center;
        }
        .status-active { background: #d9edd4; color: #237a2d; }
        .status-open { background: #dbe9ff; color: #2457b7; }
        .status-locked { background: #f3dfcf; color: #b36a1f; }
        .step-wrap {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: .75rem;
            margin: .5rem 0 1.15rem 0;
        }
        .step-item {
            flex: 1;
            text-align: center;
            position: relative;
        }
        .step-circle {
            width: 42px;
            height: 42px;
            border-radius: 999px;
            background: #e5e7eb;
            color: #374151;
            font-weight: 800;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-bottom: .5rem;
            font-size: 1rem;
        }
        .step-circle.active {
            background: #2563eb;
            color: white;
        }
        .step-circle.done {
            background: #9ec3ff;
            color: #0f2f87;
        }
        .step-label {
            font-weight: 700;
            color: #1f2937;
            font-size: .95rem;
        }
        .step-sub {
            color: #4b5563;
            font-size: .9rem;
        }
        .legend-row {
            display: flex;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
            margin-top: .35rem;
            color: #4b5563;
            font-size: .95rem;
        }
        .legend-chip {
            display: inline-flex;
            align-items: center;
            gap: .45rem;
        }
        .legend-box {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            display: inline-block;
            border: 2px solid #cbd5e1;
        }
        .mini-note {
            background: #f2f7ff;
            border: 1px solid #d7e4ff;
            border-radius: 12px;
            padding: .9rem;
            color: #334155;
            font-size: .96rem;
        }
        .foot-note {
            background: #eef4fb;
            border: 1px solid #d8e2f0;
            color: #475569;
            border-radius: 10px;
            padding: .75rem 1rem;
            margin-top: .8rem;
        }
        div[data-testid="stMetric"] {
            background: #fbfdff;
            border: 1px solid #dbe5f0;
            padding: .75rem .85rem;
            border-radius: 14px;
        }
        div[data-testid="stForm"] {
            background: #ffffff;
            border: 1px solid #d8dee9;
            border-radius: 16px;
            padding: 1rem;
            box-shadow: 0 4px 14px rgba(15,23,42,.04);
        }
        .locked-note {
            color: #9ca3af;
            font-style: italic;
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
DEFAULT_C1_QUALITY = 0.95
DEFAULT_C2_QUALITY = 1.03
DEFAULT_NOISE_BOUND = 0.10

BASE_MARKET_DEMAND_DEFAULT = {
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

EXTRA_LOGISTICS_COST_DEFAULT = {
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

BASE_PRICE_TEMPLATE_DEFAULT = {
    "ours": {"A": 55, "B": 58, "C": 60, "D": 61},
    "C1": {"A": 57, "B": 58},
    "C2": {"C": 60, "D": 61},
}


@dataclass(frozen=True)
class RoundScenario:
    round_no: int
    title: str
    opens_market: str | None = None
    c1_discount_pct: float = 0.0
    c2_discount_pct: float = 0.0


ROUND_SCENARIOS: List[RoundScenario] = [
    RoundScenario(1, "Launch in HQ market", opens_market="A"),
    RoundScenario(2, "Expand to a second market", opens_market="B"),
    RoundScenario(3, "Competitor 1 discount shock", opens_market="C", c1_discount_pct=0.30),
    RoundScenario(4, "Competitor 2 discount shock", opens_market="D", c2_discount_pct=0.15),
    RoundScenario(5, "Final optimization across all open markets", opens_market=None),
]


# ============================================================
# State helpers
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
        st.session_state.default_prices = BASE_PRICE_TEMPLATE_DEFAULT["ours"].copy()
    if "base_market_demand" not in st.session_state:
        st.session_state.base_market_demand = BASE_MARKET_DEMAND_DEFAULT.copy()
    if "extra_logistics_cost" not in st.session_state:
        st.session_state.extra_logistics_cost = EXTRA_LOGISTICS_COST_DEFAULT.copy()
    if "c1_prices" not in st.session_state:
        st.session_state.c1_prices = BASE_PRICE_TEMPLATE_DEFAULT["C1"].copy()
    if "c2_prices" not in st.session_state:
        st.session_state.c2_prices = BASE_PRICE_TEMPLATE_DEFAULT["C2"].copy()
    if "c1_quality" not in st.session_state:
        st.session_state.c1_quality = DEFAULT_C1_QUALITY
    if "c2_quality" not in st.session_state:
        st.session_state.c2_quality = DEFAULT_C2_QUALITY
    if "noise_bound" not in st.session_state:
        st.session_state.noise_bound = DEFAULT_NOISE_BOUND
    if "round3_c1_discount" not in st.session_state:
        st.session_state.round3_c1_discount = 0.30
    if "round4_c2_discount" not in st.session_state:
        st.session_state.round4_c2_discount = 0.15


init_state()


def reset_simulation() -> None:
    st.session_state.round_idx = 0
    st.session_state.history = []
    st.session_state.last_result = None


def reset_instructor_defaults() -> None:
    st.session_state.base_market_demand = BASE_MARKET_DEMAND_DEFAULT.copy()
    st.session_state.extra_logistics_cost = EXTRA_LOGISTICS_COST_DEFAULT.copy()
    st.session_state.c1_prices = BASE_PRICE_TEMPLATE_DEFAULT["C1"].copy()
    st.session_state.c2_prices = BASE_PRICE_TEMPLATE_DEFAULT["C2"].copy()
    st.session_state.default_prices = BASE_PRICE_TEMPLATE_DEFAULT["ours"].copy()
    st.session_state.c1_quality = DEFAULT_C1_QUALITY
    st.session_state.c2_quality = DEFAULT_C2_QUALITY
    st.session_state.noise_bound = DEFAULT_NOISE_BOUND
    st.session_state.round3_c1_discount = 0.30
    st.session_state.round4_c2_discount = 0.15


# ============================================================
# Logic
# ============================================================
def active_markets_for_round(round_no: int) -> List[str]:
    if round_no <= 1:
        return ["A"]
    if round_no == 2:
        return ["A", "B"]
    if round_no == 3:
        return ["A", "B", "C"]
    return ["A", "B", "C", "D"]


def manufacturing_unit_cost(total_units: float) -> float:
    if total_units > 3000:
        return 20.0
    if total_units > 1000:
        return 23.0
    return 25.0


def market_competitor_price(market: str, round_no: int) -> float:
    if "C1" in COMPETITOR_COVERAGE[market]:
        base_price = st.session_state.c1_prices[market]
        if round_no == 3:
            return round(base_price * (1 - st.session_state.round3_c1_discount), 2)
        return round(base_price, 2)
    if "C2" in COMPETITOR_COVERAGE[market]:
        base_price = st.session_state.c2_prices[market]
        if round_no == 4:
            return round(base_price * (1 - st.session_state.round4_c2_discount), 2)
        return round(base_price, 2)
    raise ValueError(f"No competitor configured for market {market}")


def market_competitor_quality(market: str) -> float:
    return st.session_state.c1_quality if "C1" in COMPETITOR_COVERAGE[market] else st.session_state.c2_quality


def base_demand_per_firm(market: str) -> float:
    num_competitors = 1 + len(COMPETITOR_COVERAGE[market])
    return st.session_state.base_market_demand[market] / num_competitors


def quality_factor(our_quality: float, competitor_quality: float) -> float:
    ratio = max(our_quality / competitor_quality, 0.01)
    return ratio ** 0.9


def price_factor(our_price: float, competitor_price: float, market: str) -> float:
    own_component = max(our_price, 1.0) ** (-0.11 * OWN_PRICE_SENSITIVITY[market])
    competitor_component = max(competitor_price, 1.0) ** (0.07 * COMP_PRICE_SENSITIVITY[market])
    return own_component * competitor_component


def hq_advantage_factor(market: str) -> float:
    return 1.06 if market == "A" else 1.0


def compute_market_quantity(
    market: str,
    our_price: float,
    round_no: int,
    our_quality: float = OUR_QUALITY,
    rng: random.Random | None = None,
) -> Dict[str, float | str]:
    competitor_price = market_competitor_price(market, round_no)
    competitor_quality = market_competitor_quality(market)
    base_demand = base_demand_per_firm(market)

    deterministic_quantity = (
        base_demand
        * price_factor(our_price, competitor_price, market)
        * quality_factor(our_quality, competitor_quality)
        * hq_advantage_factor(market)
    )

    if rng is None:
        rng = random.Random()
    noise_multiplier = rng.uniform(1 - st.session_state.noise_bound, 1 + st.session_state.noise_bound)
    quantity = max(deterministic_quantity * noise_multiplier, 0.0)

    return {
        "market": market,
        "base_demand": round(base_demand, 2),
        "market_size": float(st.session_state.base_market_demand[market]),
        "our_price": round(our_price, 2),
        "competitor_price": round(competitor_price, 2),
        "our_quality": round(our_quality, 3),
        "competitor_quality": round(competitor_quality, 3),
        "noise_multiplier": round(noise_multiplier, 4),
        "quantity": round(quantity, 2),
    }


def compute_round_results(prices: Dict[str, float], round_no: int, rng_seed: int) -> Dict[str, object]:
    rng = random.Random(rng_seed)
    active_markets = active_markets_for_round(round_no)
    market_results: List[Dict[str, float | str]] = []

    for market in active_markets:
        market_results.append(
            compute_market_quantity(
                market=market,
                our_price=float(prices[market]),
                round_no=round_no,
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
        uvc = base_uvc + st.session_state.extra_logistics_cost[market]
        revenue = price * quantity
        variable_cost = uvc * quantity
        profit = revenue - variable_cost

        competitor_price = float(row["competitor_price"])
        competitor_quantity = compute_market_quantity(
            market=market,
            our_price=competitor_price,
            round_no=round_no,
            rng=random.Random(rng_seed + 100 + ord(market)),
        )["quantity"]
        total_market_units = quantity + float(competitor_quantity)
        market_share = quantity / total_market_units if total_market_units > 0 else 0.0

        row["uvc"] = round(uvc, 2)
        row["revenue"] = round(revenue, 2)
        row["variable_cost"] = round(variable_cost, 2)
        row["profit"] = round(profit, 2)
        row["market_share"] = round(market_share, 4)

        total_revenue += revenue
        total_variable_cost += variable_cost
        total_profit += profit

    return {
        "round_no": round_no,
        "title": ROUND_SCENARIOS[round_no - 1].title,
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


def market_status(market: str, round_no: int) -> str:
    active = active_markets_for_round(round_no)
    if market in active:
        return "active" if market == active[-1] else "open"
    return "locked"


# ============================================================
# Sidebar instructor controls
# ============================================================
with st.sidebar:
    st.markdown("## ⚙️ Instructor Controls")
    st.text_input("Team / student name", key="team_name")
    st.number_input("Noise seed base", min_value=1, max_value=999999, key="noise_seed_base")

    with st.expander("Scenario Configuration", expanded=True):
        dm1, dm2 = st.columns(2)
        with dm1:
            st.session_state.base_market_demand["A"] = st.number_input("Demand A", 500, 3000, int(st.session_state.base_market_demand["A"]), 50)
            st.session_state.base_market_demand["B"] = st.number_input("Demand B", 500, 3000, int(st.session_state.base_market_demand["B"]), 50)
        with dm2:
            st.session_state.base_market_demand["C"] = st.number_input("Demand C", 500, 3000, int(st.session_state.base_market_demand["C"]), 50)
            st.session_state.base_market_demand["D"] = st.number_input("Demand D", 500, 3000, int(st.session_state.base_market_demand["D"]), 50)

    with st.expander("Competitor Prices", expanded=False):
        cp1, cp2 = st.columns(2)
        with cp1:
            st.session_state.c1_prices["A"] = st.number_input("C1 price in A", 20, 100, int(st.session_state.c1_prices["A"]), 1)
            st.session_state.c1_prices["B"] = st.number_input("C1 price in B", 20, 100, int(st.session_state.c1_prices["B"]), 1)
        with cp2:
            st.session_state.c2_prices["C"] = st.number_input("C2 price in C", 20, 100, int(st.session_state.c2_prices["C"]), 1)
            st.session_state.c2_prices["D"] = st.number_input("C2 price in D", 20, 100, int(st.session_state.c2_prices["D"]), 1)

    with st.expander("Discount Events", expanded=False):
        st.session_state.round3_c1_discount = st.slider("Round 3 – C1 discount", 0.0, 0.6, float(st.session_state.round3_c1_discount), 0.05)
        st.session_state.round4_c2_discount = st.slider("Round 4 – C2 discount", 0.0, 0.6, float(st.session_state.round4_c2_discount), 0.05)

    with st.expander("Noise and Quality", expanded=False):
        st.session_state.noise_bound = st.slider("Noise level", 0.0, 0.2, float(st.session_state.noise_bound), 0.01)
        st.session_state.c1_quality = st.slider("C1 quality vs us", 0.7, 1.2, float(st.session_state.c1_quality), 0.01)
        st.session_state.c2_quality = st.slider("C2 quality vs us", 0.7, 1.2, float(st.session_state.c2_quality), 0.01)

    if st.button("Reset simulation", use_container_width=True):
        reset_simulation()
        st.rerun()
    if st.button("Reset instructor defaults", use_container_width=True):
        reset_instructor_defaults()
        st.rerun()


# ============================================================
# Header
# ============================================================
st.markdown(
    """
    <div class="topbar">
        <h1>PRICING SIMULATION – PILOT V2</h1>
        <p>Multimarket Pricing Strategy</p>
    </div>
    """,
    unsafe_allow_html=True,
)

completed = st.session_state.round_idx >= TOTAL_ROUNDS
current_round_no = min(st.session_state.round_idx + 1, TOTAL_ROUNDS)
summary = summarize_history(st.session_state.history)
active_markets = active_markets_for_round(current_round_no if not completed else TOTAL_ROUNDS)
active_market = active_markets[-1] if active_markets else "A"


# ============================================================
# Top layout: round rail + market/about panels
# ============================================================
main_left, main_right = st.columns([2.15, 1.1], gap="large")

with main_left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f"## ROUND {current_round_no} OF {TOTAL_ROUNDS}")
    st.markdown(f"**Active Market: {active_market}**")
    st.write("You will add one new market in each round.")

    steps = [
        (1, "Market A", ""),
        (2, "Add Market B", ""),
        (3, "Add Market C", ""),
        (4, "Add Market D", ""),
        (5, "Final Results", ""),
    ]
    step_html = ['<div class="step-wrap">']
    for step_no, label, sub in steps:
        if step_no < current_round_no:
            css = "done"
        elif step_no == current_round_no and not completed:
            css = "active"
        else:
            css = ""
        step_html.append(
            f'''<div class="step-item"><div class="step-circle {css}">{step_no}</div><div class="step-label">{label}</div></div>'''
        )
    step_html.append('</div>')
    st.markdown("".join(step_html), unsafe_allow_html=True)

    st.markdown('<div class="market-grid-title">MARKET OVERVIEW</div>', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    for idx, market in enumerate(MARKETS):
        holder = g1 if idx % 2 == 0 else g2
        with holder:
            status = market_status(market, current_round_no if not completed else TOTAL_ROUNDS)
            demand = st.session_state.base_market_demand[market]
            c1_text = f"${market_competitor_price(market, current_round_no if not completed else TOTAL_ROUNDS):.2f}" if "C1" in COMPETITOR_COVERAGE[market] else "—"
            c2_text = f"${market_competitor_price(market, current_round_no if not completed else TOTAL_ROUNDS):.2f}" if "C2" in COMPETITOR_COVERAGE[market] else "—"
            sub = "(Your HQ Market)" if market == "A" else ""
            card_class = "active" if status == "active" else ("unlocked" if status == "open" else "locked")
            status_class = "status-active" if status == "active" else ("status-open" if status == "open" else "status-locked")
            status_text = "ACTIVE" if status == "active" else ("OPEN" if status == "open" else "LOCKED")
            st.markdown(
                f"""
                <div class="market-card {card_class}">
                    <div class="market-name">{market}</div>
                    <div class="market-sub">{sub}</div>
                    <div class="market-stat">Total Market Demand</div>
                    <div class="market-demand">{demand:,.0f}</div>
                    <div class="market-stat">units</div>
                    <div class="market-stat" style="margin-top:1rem;">Competitor Prices</div>
                    <div class="market-stat">C1: <b>{c1_text}</b> &nbsp;&nbsp;&nbsp; C2: <b>{c2_text}</b></div>
                    <div class="status-bar {status_class}">{status_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="legend-row">
            <span class="legend-chip"><span class="legend-box" style="background:#eef7ec;border-color:#6db36d;"></span>Active</span>
            <span class="legend-chip"><span class="legend-box" style="background:#f8fbff;border-color:#a8c5ff;"></span>Open</span>
            <span class="legend-chip"><span class="legend-box" style="background:#faf7f4;border-color:#ead7c4;"></span>Locked</span>
            <span class="legend-chip"><b>C1</b>: Competitor 1</span>
            <span class="legend-chip"><b>C2</b>: Competitor 2</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with main_right:
    st.markdown('<div class="section-card"><div class="section-title">ABOUT THE MARKETS</div>', unsafe_allow_html=True)
    st.write("Our HQ is in Market A, so we have a natural advantage there.")
    st.write("Competitor 1 (C1) is based in Market B.")
    st.write("Competitor 2 (C2) is based in Market D.")
    st.write("")
    st.write("Competitors cannot expand beyond their regions:")
    st.markdown("- C1 only competes in Markets A & B")
    st.markdown("- C2 only competes in Markets C & D")
    st.write("")
    st.write("**Product Quality (vs. Ours)**")
    st.markdown(f"- Competitor 1 (C1): ~{st.session_state.c1_quality * 100:.0f}% of our quality")
    st.markdown(f"- Competitor 2 (C2): ~{st.session_state.c2_quality * 100:.0f}% of our quality")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">ROUND EVENTS</div>', unsafe_allow_html=True)
    st.write(f"Round 3: Competitor 1 (C1) gives {st.session_state.round3_c1_discount * 100:.0f}% discount")
    st.write(f"Round 4: Competitor 2 (C2) gives {st.session_state.round4_c2_discount * 100:.0f}% discount")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">HOW IT WORKS</div>', unsafe_allow_html=True)
    st.markdown("- Set your price for the active market, and keep pricing open markets in later rounds.")
    st.markdown("- Observe revenue, profit, and market share after each round.")
    st.markdown("- Each round, one new market opens.")
    st.markdown("- Your goal is to maximize total profit across all markets.")
    st.markdown('</div>', unsafe_allow_html=True)


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
            market_rows.append({"round_no": round_result["round_no"], **market_result})

    rounds_df = pd.DataFrame(history_rows)
    markets_df = pd.DataFrame(market_rows)

    st.markdown('<div class="section-card"><div class="section-title">FINAL PERFORMANCE</div>', unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("Total revenue", f"${summary['cumulative_revenue']:,.0f}")
    b.metric("Total profit", f"${summary['cumulative_profit']:,.0f}")
    c.metric("Total units", f"{summary['cumulative_units']:,.0f}")
    d.metric("Average profit / round", f"${summary['avg_profit_per_round']:,.0f}")
    st.dataframe(rounds_df, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    charts1, charts2, charts3 = st.columns(3)
    latest_markets = markets_df[markets_df["round_no"] == markets_df["round_no"].max()].copy()
    latest_markets = latest_markets.set_index("market")
    with charts1:
        st.markdown('<div class="section-card"><div class="section-title">MARKET SHARE (%)</div>', unsafe_allow_html=True)
        st.bar_chart((latest_markets["market_share"] * 100))
        st.markdown('</div>', unsafe_allow_html=True)
    with charts2:
        st.markdown('<div class="section-card"><div class="section-title">REVENUE (USD)</div>', unsafe_allow_html=True)
        st.bar_chart(latest_markets["revenue"])
        st.markdown('</div>', unsafe_allow_html=True)
    with charts3:
        st.markdown('<div class="section-card"><div class="section-title">PROFIT (USD)</div>', unsafe_allow_html=True)
        st.bar_chart(latest_markets["profit"])
        st.markdown('</div>', unsafe_allow_html=True)

    csv = markets_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download detailed results CSV",
        data=csv,
        file_name="pricing_simulation_pilot_v2_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.stop()


# ============================================================
# Active round view
# ============================================================
round_no = current_round_no
round_title = ROUND_SCENARIOS[round_no - 1].title
open_markets = active_markets_for_round(round_no)
current_active_market = open_markets[-1]

lower_left, lower_right = st.columns([2.15, 1.1], gap="large")

with lower_left:
    st.markdown(f'<div class="section-title">SET YOUR PRICES — ROUND {round_no}</div>', unsafe_allow_html=True)
    with st.form("round_form"):
        form_left, form_right = st.columns([1.05, 1.3], gap="large")

        with form_left:
            st.write(f"### Active Focus: Market {current_active_market}")
            price_inputs: Dict[str, float] = {}
            for market in open_markets:
                price_inputs[market] = st.slider(
                    f"Your price in Market {market}",
                    min_value=20,
                    max_value=85,
                    value=int(st.session_state.default_prices[market]),
                    step=1,
                )
            for market in MARKETS:
                if market not in open_markets:
                    st.markdown(f"<div class='locked-note'>Market {market} is still locked this round.</div>", unsafe_allow_html=True)

            st.markdown(
                f"""
                <div class="mini-note">
                    Consider competitor prices, market demand, and your position in each open market.
                </div>
                """,
                unsafe_allow_html=True,
            )

        with form_right:
            snapshot_rows = []
            for market in open_markets:
                snapshot_rows.append({
                    "Market": market,
                    "Total Market Demand": st.session_state.base_market_demand[market],
                    "Competitor Price": market_competitor_price(market, round_no),
                    "Your Base Cost": manufacturing_unit_cost(1),
                    "Additional Var. Cost": st.session_state.extra_logistics_cost[market],
                })
            snapshot_df = pd.DataFrame(snapshot_rows)
            st.write(f"### Round {round_no} Snapshot")
            st.dataframe(snapshot_df, use_container_width=True, hide_index=True)

        submitted = st.form_submit_button("Submit Prices for This Round", use_container_width=True)

    if submitted:
        for market in open_markets:
            st.session_state.default_prices[market] = price_inputs[market]
        round_result = compute_round_results(
            prices=price_inputs,
            round_no=round_no,
            rng_seed=st.session_state.noise_seed_base + round_no,
        )
        st.session_state.last_result = round_result
        st.session_state.history.append(round_result)
        st.session_state.round_idx += 1
        st.rerun()

    st.markdown('<div class="section-card"><div class="section-title">YOUR PERFORMANCE (CURRENT ROUND)</div>', unsafe_allow_html=True)
    if st.session_state.last_result is None:
        st.info("Submit the first round to populate the performance charts.")
    else:
        latest_df = pd.DataFrame(st.session_state.last_result["markets"]).set_index("market")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.write("**Market Share (%)**")
            st.bar_chart(latest_df["market_share"] * 100)
        with c2:
            st.write("**Revenue (USD)**")
            st.bar_chart(latest_df["revenue"])
        with c3:
            st.write("**Profit (USD)**")
            st.bar_chart(latest_df["profit"])
    st.markdown('</div>', unsafe_allow_html=True)

with lower_right:
    st.markdown('<div class="section-card"><div class="section-title">LATEST RESULT</div>', unsafe_allow_html=True)
    if st.session_state.last_result is None:
        st.info("No round completed yet.")
    else:
        latest = st.session_state.last_result
        x1, x2, x3 = st.columns(3)
        x1.metric("Round profit", f"${float(latest['total_profit']):,.0f}")
        x2.metric("Round revenue", f"${float(latest['total_revenue']):,.0f}")
        x3.metric("Units sold", f"{float(latest['total_units']):,.0f}")
        st.write(market_feedback(latest))
        latest_table = pd.DataFrame(latest["markets"])[[
            "market", "our_price", "competitor_price", "quantity", "uvc", "revenue", "profit", "market_share"
        ]].copy()
        latest_table["market_share"] = (latest_table["market_share"] * 100).round(1)
        st.dataframe(latest_table, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">CUMULATIVE TRACKING</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Cumulative profit", f"${summary['cumulative_profit']:,.0f}")
    m2.metric("Cumulative revenue", f"${summary['cumulative_revenue']:,.0f}")
    m3.metric("Average / round", f"${summary['avg_profit_per_round']:,.0f}")
    if st.session_state.history:
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
    st.markdown('</div>', unsafe_allow_html=True)


st.markdown(
    f"""
    <div class="foot-note">
        Note: Demand includes up to ±{int(st.session_state.noise_bound * 100)}% random market variation.
    </div>
    """,
    unsafe_allow_html=True,
)
