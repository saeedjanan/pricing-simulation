import math
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
import streamlit as st


# ============================================================
# Page setup
# ============================================================
st.set_page_config(
    page_title="Pricing Simulation Studio",
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
        .main {
            background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1250px;
        }
        .hero {
            padding: 1.25rem 1.5rem;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(37,99,235,.25), rgba(16,185,129,.18));
            border: 1px solid rgba(255,255,255,.08);
            box-shadow: 0 10px 30px rgba(0,0,0,.18);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2rem;
            color: #f9fafb;
        }
        .hero p {
            margin: .35rem 0 0 0;
            color: #d1d5db;
            font-size: 1rem;
        }
        .card {
            background: rgba(255,255,255,.04);
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 18px;
            padding: 1rem 1rem .85rem 1rem;
            box-shadow: 0 8px 20px rgba(0,0,0,.12);
            margin-bottom: .9rem;
        }
        .card-title {
            color: #f3f4f6;
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: .4rem;
        }
        .muted {
            color: #cbd5e1;
            font-size: .96rem;
        }
        .pill {
            display: inline-block;
            padding: .25rem .6rem;
            border-radius: 999px;
            background: rgba(59,130,246,.18);
            border: 1px solid rgba(59,130,246,.35);
            color: #dbeafe;
            font-size: .85rem;
            margin-right: .4rem;
            margin-top: .25rem;
        }
        .result-good {
            padding: .9rem 1rem;
            border-radius: 14px;
            background: rgba(16,185,129,.12);
            border: 1px solid rgba(16,185,129,.35);
            color: #d1fae5;
            margin-top: .7rem;
        }
        .result-bad {
            padding: .9rem 1rem;
            border-radius: 14px;
            background: rgba(239,68,68,.10);
            border: 1px solid rgba(239,68,68,.35);
            color: #fee2e2;
            margin-top: .7rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,.04);
            border: 1px solid rgba(255,255,255,.08);
            padding: .75rem .9rem;
            border-radius: 16px;
        }
        div[data-testid="stForm"] {
            background: rgba(255,255,255,.04);
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 18px;
            padding: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Data and engine
# ============================================================
@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    base_demand: float
    unit_cost: float
    competitor_price: float
    own_price_sensitivity: float
    competitor_price_effect: float
    demand_shock: float = 0.0


DEFAULT_SCENARIOS: List[Scenario] = [
    Scenario(
        name="Balanced Market",
        description="Demand is steady and customers compare prices, but not aggressively.",
        base_demand=1000,
        unit_cost=22,
        competitor_price=45,
        own_price_sensitivity=8.0,
        competitor_price_effect=5.0,
        demand_shock=0.0,
    ),
    Scenario(
        name="Price-Sensitive Segment",
        description="Consumers are more price conscious this round, so small price moves matter more.",
        base_demand=1050,
        unit_cost=22,
        competitor_price=44,
        own_price_sensitivity=11.0,
        competitor_price_effect=5.5,
        demand_shock=-40.0,
    ),
    Scenario(
        name="Strong Demand",
        description="Category demand expands and buyers tolerate somewhat higher prices.",
        base_demand=1150,
        unit_cost=23,
        competitor_price=48,
        own_price_sensitivity=7.0,
        competitor_price_effect=4.5,
        demand_shock=80.0,
    ),
    Scenario(
        name="Competitor Discounting",
        description="The rival cuts price, putting stronger pressure on your demand.",
        base_demand=1000,
        unit_cost=23,
        competitor_price=40,
        own_price_sensitivity=8.5,
        competitor_price_effect=6.0,
        demand_shock=0.0,
    ),
    Scenario(
        name="Premium Window",
        description="Customers value the category more this round, but only within reason.",
        base_demand=1125,
        unit_cost=24,
        competitor_price=50,
        own_price_sensitivity=6.5,
        competitor_price_effect=5.5,
        demand_shock=50.0,
    ),
]


def compute_quantity(price: float, scenario: Scenario) -> float:
    quantity = (
        scenario.base_demand
        - scenario.own_price_sensitivity * price
        + scenario.competitor_price_effect * scenario.competitor_price
        + scenario.demand_shock
    )
    return max(quantity, 0.0)


def compute_results(price: float, scenario: Scenario) -> Dict[str, float | str]:
    quantity = compute_quantity(price, scenario)
    revenue = price * quantity
    variable_cost = scenario.unit_cost * quantity
    profit = revenue - variable_cost
    margin_per_unit = price - scenario.unit_cost

    competitor_quantity = compute_quantity(scenario.competitor_price, scenario)
    competitor_profit = (
        scenario.competitor_price * competitor_quantity
        - scenario.unit_cost * competitor_quantity
    )

    total_market = quantity + competitor_quantity
    market_share = quantity / total_market if total_market > 0 else 0.0

    return {
        "scenario": scenario.name,
        "price": round(price, 2),
        "quantity": round(quantity, 2),
        "revenue": round(revenue, 2),
        "variable_cost": round(variable_cost, 2),
        "profit": round(profit, 2),
        "margin_per_unit": round(margin_per_unit, 2),
        "competitor_price": round(scenario.competitor_price, 2),
        "competitor_profit": round(competitor_profit, 2),
        "market_share": round(market_share, 4),
    }


def price_feedback(result: Dict[str, float | str]) -> str:
    margin = float(result["margin_per_unit"])
    share = float(result["market_share"])
    profit = float(result["profit"])

    if profit <= 0:
        return "This choice destroyed value. Your price likely failed to balance margin and volume."
    if margin < 5:
        return "You captured volume, but your unit margin is thin. Consider whether a modest price increase could improve profit."
    if share < 0.45:
        return "You protected margin but lost too much of the market. Your price may be too aggressive."
    return "This is a healthy balance of margin and demand. You are competing effectively while remaining profitable."


# ============================================================
# Session state
# ============================================================
def init_state() -> None:
    if "round_idx" not in st.session_state:
        st.session_state.round_idx = 0
    if "history" not in st.session_state:
        st.session_state.history = []
    if "team_name" not in st.session_state:
        st.session_state.team_name = ""
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "custom_scenarios" not in st.session_state:
        st.session_state.custom_scenarios = DEFAULT_SCENARIOS.copy()


init_state()


def reset_simulation() -> None:
    st.session_state.round_idx = 0
    st.session_state.history = []
    st.session_state.last_result = None


def current_scenarios() -> List[Scenario]:
    return st.session_state.custom_scenarios


# ============================================================
# Sidebar controls
# ============================================================
st.sidebar.markdown("## ⚙️ Instructor Controls")
st.sidebar.caption("Use these settings to shape the market before students play.")

scenario_names = [s.name for s in DEFAULT_SCENARIOS]
selected_name = st.sidebar.selectbox("Edit scenario", scenario_names, index=0)
selected_index = scenario_names.index(selected_name)
base_scenario = current_scenarios()[selected_index]

with st.sidebar.expander("Customize selected scenario", expanded=True):
    edited_base_demand = st.slider(
        "Base demand",
        min_value=600,
        max_value=1600,
        value=int(base_scenario.base_demand),
        step=25,
    )
    edited_unit_cost = st.slider(
        "Unit cost",
        min_value=5,
        max_value=80,
        value=int(base_scenario.unit_cost),
        step=1,
    )
    edited_competitor_price = st.slider(
        "Competitor price",
        min_value=10,
        max_value=120,
        value=int(base_scenario.competitor_price),
        step=1,
    )
    edited_sensitivity = st.slider(
        "Own price sensitivity",
        min_value=1.0,
        max_value=20.0,
        value=float(base_scenario.own_price_sensitivity),
        step=0.5,
    )
    edited_comp_effect = st.slider(
        "Competitor price effect",
        min_value=0.0,
        max_value=12.0,
        value=float(base_scenario.competitor_price_effect),
        step=0.5,
    )
    edited_shock = st.slider(
        "Demand shock",
        min_value=-300,
        max_value=300,
        value=int(base_scenario.demand_shock),
        step=10,
    )

    if st.button("Apply scenario changes", use_container_width=True):
        updated = current_scenarios().copy()
        updated[selected_index] = Scenario(
            name=base_scenario.name,
            description=base_scenario.description,
            base_demand=edited_base_demand,
            unit_cost=edited_unit_cost,
            competitor_price=edited_competitor_price,
            own_price_sensitivity=edited_sensitivity,
            competitor_price_effect=edited_comp_effect,
            demand_shock=edited_shock,
        )
        st.session_state.custom_scenarios = updated
        st.sidebar.success("Scenario updated.")

if st.sidebar.button("Reset scenarios to default", use_container_width=True):
    st.session_state.custom_scenarios = DEFAULT_SCENARIOS.copy()
    st.sidebar.success("All scenarios reset.")

st.sidebar.markdown("---")
st.sidebar.text_input("Team / student name", key="team_name")
if st.sidebar.button("Restart simulation", use_container_width=True):
    reset_simulation()
    st.rerun()


# ============================================================
# Header
# ============================================================
st.markdown(
    f"""
    <div class="hero">
        <h1>📈 Pricing Simulation Studio</h1>
        <p>Interactive marketing pricing game with instructor controls, round-by-round decisions, and performance analytics.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

scenarios = current_scenarios()
round_idx = st.session_state.round_idx
completed = round_idx >= len(scenarios)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Rounds completed", f"{min(round_idx, len(scenarios))}/{len(scenarios)}")
k2.metric("Team", st.session_state.team_name if st.session_state.team_name else "Not set")
k3.metric(
    "Cumulative profit",
    f"${sum(float(h['profit']) for h in st.session_state.history):,.0f}" if st.session_state.history else "$0",
)
k4.metric(
    "Average market share",
    f"{(sum(float(h['market_share']) for h in st.session_state.history) / len(st.session_state.history) * 100):.1f}%"
    if st.session_state.history else "0.0%",
)


# ============================================================
# Completed state
# ============================================================
if completed:
    st.success("Simulation completed.")

    df = pd.DataFrame(st.session_state.history)
    summary_left, summary_right = st.columns([1.1, 1])

    with summary_left:
        st.markdown('<div class="card"><div class="card-title">Final performance</div></div>', unsafe_allow_html=True)
        a, b, c = st.columns(3)
        a.metric("Total profit", f"${df['profit'].sum():,.0f}")
        b.metric("Average price", f"${df['price'].mean():,.2f}")
        c.metric("Average share", f"{df['market_share'].mean() * 100:,.1f}%")
        st.line_chart(df.set_index(pd.Index(range(1, len(df) + 1)))[["profit", "price"]])

    with summary_right:
        st.markdown('<div class="card"><div class="card-title">Round history</div></div>', unsafe_allow_html=True)
        display_df = df[["scenario", "price", "quantity", "revenue", "profit", "market_share"]].copy()
        display_df["market_share"] = (display_df["market_share"] * 100).round(1)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download results as CSV",
        data=csv,
        file_name="pricing_simulation_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.stop()


# ============================================================
# Main two-column interface
# ============================================================
scenario = scenarios[round_idx]
left, right = st.columns([1.1, 1], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<div class="card-title">Round {round_idx + 1}: {scenario.name}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="muted">{scenario.description}</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="margin-top:.7rem;">
            <span class="pill">Unit cost: ${scenario.unit_cost:.0f}</span>
            <span class="pill">Competitor price: ${scenario.competitor_price:.0f}</span>
            <span class="pill">Base demand: {scenario.base_demand:.0f}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("pricing_decision"):
        st.markdown("#### Make your pricing decision")
        price = st.slider(
            "Choose your price",
            min_value=10,
            max_value=120,
            value=int(scenario.competitor_price),
            step=1,
            help="Set your selling price for this round.",
        )

        with st.expander("Advanced view", expanded=False):
            preview_quantity = compute_quantity(float(price), scenario)
            st.write(f"Estimated quantity at this price: **{preview_quantity:,.0f}**")
            st.caption("This preview uses the current response function and is visible here only for testing and calibration.")

        submitted = st.form_submit_button("Submit decision", use_container_width=True)

    if submitted:
        result = compute_results(float(price), scenario)
        st.session_state.history.append(result)
        st.session_state.last_result = result
        st.session_state.round_idx += 1
        st.rerun()

with right:
    st.markdown('<div class="card"><div class="card-title">Latest result</div></div>', unsafe_allow_html=True)

    if st.session_state.last_result is None:
        st.info("Submit your first pricing decision to see results.")
    else:
        result = st.session_state.last_result
        r1, r2 = st.columns(2)
        r1.metric("Profit", f"${float(result['profit']):,.0f}")
        r2.metric("Revenue", f"${float(result['revenue']):,.0f}")

        r3, r4 = st.columns(2)
        r3.metric("Quantity", f"{float(result['quantity']):,.0f}")
        r4.metric("Market share", f"{float(result['market_share']) * 100:,.1f}%")

        msg = price_feedback(result)
        if float(result["profit"]) >= float(result["competitor_profit"]):
            st.markdown(f'<div class="result-good">✅ {msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-bad">⚠️ {msg}</div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">Performance dashboard</div></div>', unsafe_allow_html=True)
    if st.session_state.history:
        df = pd.DataFrame(st.session_state.history)
        chart_df = df[["profit", "price", "market_share"]].copy()
        st.line_chart(chart_df)

        compact = df[["scenario", "price", "profit", "market_share"]].copy()
        compact["market_share"] = (compact["market_share"] * 100).round(1)
        st.dataframe(compact, use_container_width=True, hide_index=True)
    else:
        st.caption("Your dashboard will appear after the first submitted round.")
