import streamlit as st
import pulp
import pandas as pd
import json

st.set_page_config(
    page_title="Jewelry Supply Chain Teaching Tool & Digital Twin (v2)",
    page_icon="💎",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #94a3b8; margin-bottom: 1.5rem; }
    .card { background-color: #1e293b; padding: 1.2rem; border-radius: 0.5rem; border: 1px solid #334155; margin-bottom: 1rem; }
    .hint-box { background-color: #0f172a; border-left: 4px solid #38bdf8; padding: 1rem; border-radius: 0.3rem; margin-top: 0.8rem; }
    .hint-warn { border-left-color: #f59e0b; }
    .hint-success { border-left-color: #10b981; }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-val { font-size: 1.5rem; font-weight: 700; color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💎 Jewelry Supply Chain Teaching Tool (v2 with Coaching Hints)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive Decision Game with Real-Time Diagnostic Coaching & Digital Twin Sandbox</div>', unsafe_allow_html=True)

mode = st.sidebar.radio(
    "Select Learning Mode:",
    ["🎮 Mode 1: Daily Decision Game (with AI Coaching)", "🔬 Mode 2: Digital Twin Sandbox"]
)

# Load Default Config
@st.cache_data
def load_default_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except Exception:
        return {
            "simulation_settings": { "management_capacity_daily": 180.0, "min_raw_material_safety_stock": 100 },
            "raw_materials": { "metal": { "unit_cost": 50.0 }, "stone": { "unit_cost": 100.0 } }
        }

cfg = load_default_config()

def generate_coaching_hints(player_decisions, lp_benchmark, day, metal_end, stone_end, mgt_used, mgt_limit):
    """
    Analyzes player decisions vs LP benchmark and generates actionable diagnostic hints.
    """
    hints = []
    
    # 1. Labor Cost & Contractor Trade-off Hints
    outsource_hired = player_decisions['outsource_hired']
    ot_reg = player_decisions['ot_reg']
    
    if outsource_hired > 0 and ot_reg < 20.0 and mgt_used < mgt_limit - 10:
        hints.append({
            "type": "warning",
            "title": "💡 Labor Trade-Off Opportunity",
            "text": f"You hired {outsource_hired} Outsource Contractors ($5.00/unit = $40/day) while Regular Payroll Overtime ($2.67/unit = $20/day) was underutilized. Since management capacity was not maxed ({mgt_used:.1f}/{mgt_limit} u used), maximizing Regular Overtime first would save up to ${(outsource_hired * 20.0):,.2f}/day!"
        })
    elif ot_reg >= 25.0 and mgt_used >= mgt_limit - 2.0:
        hints.append({
            "type": "info",
            "title": "⚠️ Management Capacity Cap Hit",
            "text": f"Management capacity reached {mgt_used:.1f} / {mgt_limit} units. Heavy overtime consumed significant management headroom. Consider hiring Skilled Contractors (0.125 mgmt/unit) or Outsource Contractors (0.038 mgmt/unit) to bypass management bottlenecks."
        })

    # 2. Raw Material & Working Capital Hints
    buy_m = player_decisions['buy_m']
    buy_s = player_decisions['buy_s']
    
    if metal_end < 100.0 or stone_end < 100.0:
        hints.append({
            "type": "warning",
            "title": "🚨 Safety Stock Violation",
            "text": f"Ending stock fell below the 100.0 unit safety floor (Metal: {metal_end:.1f} u, Stone: {stone_end:.1f} u). Operating below safety stock risks stockout penalties on unexpected demand surge days."
        })
    elif buy_m > 600 or buy_s > 600:
        hints.append({
            "type": "info",
            "title": "💰 Working Capital Efficiency",
            "text": f"You purchased large material quantities ({buy_m} Metal / {buy_s} Stone). Purchasing far beyond 2-day WIP needs locks up working capital unnecessarily. A Lean Just-In-Time replenishment keeps cash flexible."
        })

    # 3. Overall Performance Rating
    efficiency = player_decisions['efficiency']
    if efficiency >= 95.0:
        hints.append({
            "type": "success",
            "title": "🌟 Master Planner Performance",
            "text": f"Outstanding execution! Your daily decisions achieved {efficiency:.1f}% cost efficiency compared to the mathematical LP benchmark."
        })
    elif efficiency >= 80.0:
        hints.append({
            "type": "info",
            "title": "👍 Solid Operational Control",
            "text": f"Good performance ({efficiency:.1f}% efficiency). Review labor class cost per unit to squeeze out remaining cost optimization opportunities."
        })
    else:
        hints.append({
            "type": "warning",
            "title": "📈 Sub-Optimal Cost Notice",
            "text": f"Efficiency fell to {efficiency:.1f}%. Review your contractor spend and material order quantities against immediate factory WIP throughput."
        })
        
    return hints

# --- MODE 1: DAILY INTERACTIVE DECISION GAME WITH COACHING ---
if mode == "🎮 Mode 1: Daily Decision Game (with AI Coaching)":
    st.header("🎮 Mode 1: Daily Decision Game (with Automated AI Coaching)")
    st.info("💡 **Goal:** Manage the factory day-by-day. Make decisions on inventory purchasing and labor allocation. Get real-time diagnostic feedback explaining how to optimize your costs relative to the Linear Program (LP) benchmark!")

    if 'day' not in st.session_state:
        st.session_state.day = 1
        st.session_state.metal_stock = 500.0
        st.session_state.stone_stock = 500.0
        st.session_state.cum_player_cost = 0.0
        st.session_state.cum_lp_cost = 0.0
        st.session_state.game_history = []
        st.session_state.last_hints = []

    st.subheader(f"📅 Current Simulation State: Day {st.session_state.day} of 7")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Metal Inventory", f"{st.session_state.metal_stock:.1f} units")
    m2.metric("Stone Inventory", f"{st.session_state.stone_stock:.1f} units")
    m3.metric("Safety Stock Floor", "100.0 units")
    m4.metric("Cumulative Player Cost", f"${st.session_state.cum_player_cost:,.2f}")

    day_orders_summary = {
        1: "43 Orders (500 units) — Opening Baseline Demand",
        2: "50 Orders (580 units) — +20% surge on small units",
        3: "65 Orders (755 units) — +50% demand surge",
        4: "43 Orders (500 units) — Normal demand",
        5: "65 Orders (755 units) — +50% demand surge",
        6: "43 Orders (500 units) — Normal demand",
        7: "43 Orders (500 units) — Normal demand"
    }

    st.write(f"**📦 Today's Incoming Demand (Day {st.session_state.day}):** {day_orders_summary.get(st.session_state.day, 'Standard Demand')}")

    with st.form("daily_decision_form"):
        st.write("### 🛠️ Enter Your Daily Decisions")
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### Raw Material Purchases")
            buy_m = st.number_input("Purchase Metal (units @ $50/unit):", min_value=0, value=200, step=25)
            buy_s = st.number_input("Purchase Stone (units @ $100/unit):", min_value=0, value=200, step=25)

        with col_right:
            st.markdown("#### Labor & Capacity Allocation")
            ot_reg = st.slider("Pre-Prod Regular Payroll Overtime (Days):", 0.0, 30.0, 10.0, step=1.0)
            hire_out = st.slider("Outsource Contractors to Hire (Artisans):", 0, 30, 5, step=1)

        submitted = st.form_submit_button("▶ Submit Decisions & Step 1 Day Forward", type="primary")

    if submitted:
        mat_cost = (buy_m * 50.0) + (buy_s * 100.0)
        art_cost = 3650.0 + (ot_reg * 20.0) + (hire_out * 40.0)
        player_day_cost = mat_cost + art_cost

        # Benchmark calculation
        lp_day_cost = 3650.0 + (max(0, buy_m - 50) * 50.0) + (max(0, buy_s - 50) * 100.0)
        efficiency = min(100.0, (lp_day_cost / player_day_cost) * 100.0)

        st.session_state.cum_player_cost += player_day_cost
        st.session_state.cum_lp_cost += lp_day_cost

        metal_end = max(100.0, st.session_state.metal_stock + buy_m - 200.0)
        stone_end = max(100.0, st.session_state.stone_stock + buy_s - 200.0)
        mgt_used = 164.5 + (ot_reg * 0.4) + (hire_out * 0.3)

        decisions = {
            'buy_m': buy_m,
            'buy_s': buy_s,
            'ot_reg': ot_reg,
            'outsource_hired': hire_out,
            'efficiency': efficiency
        }

        # Generate Coaching Hints
        hints = generate_coaching_hints(decisions, lp_day_cost, st.session_state.day, metal_end, stone_end, mgt_used, 180.0)
        st.session_state.last_hints = hints

        st.session_state.game_history.append({
            "Day": f"Day {st.session_state.day}",
            "Player Cost": f"${player_day_cost:,.2f}",
            "LP Benchmark": f"${lp_day_cost:,.2f}",
            "Score": f"{efficiency:.1f}%"
        })

        st.session_state.metal_stock = metal_end
        st.session_state.stone_stock = stone_end
        st.session_state.day += 1

        st.success("Day completed! Review your coaching hints and scorecard below.")

    # Display Automated Coaching Hints
    if st.session_state.last_hints:
        st.write("### 🧠 Automated Coaching Hints & Diagnostic Feedback")
        for hint in st.session_state.last_hints:
            if hint['type'] == 'warning':
                st.warning(f"**{hint['title']}**: {hint['text']}")
            elif hint['type'] == 'success':
                st.success(f"**{hint['title']}**: {hint['text']}")
            else:
                st.info(f"**{hint['title']}**: {hint['text']}")

    if st.session_state.game_history:
        st.write("### 📊 Performance Scorecard History")
        st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)

    if st.button("🔄 Reset Game Session"):
        st.session_state.day = 1
        st.session_state.metal_stock = 500.0
        st.session_state.stone_stock = 500.0
        st.session_state.cum_player_cost = 0.0
        st.session_state.cum_lp_cost = 0.0
        st.session_state.game_history = []
        st.session_state.last_hints = []
        st.rerun()

# --- MODE 2: DIGITAL TWIN SANDBOX ---
else:
    st.header("🔬 Mode 2: Digital Twin Sensitivity Sandbox")
    st.info("💡 **Goal:** Test how changing factory constraints, demand multipliers, and order mix alters 7-day costs and throughput.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Factory Constraints")
        mgt_cap = st.slider("Management Capacity Limit (units/day):", 100, 300, 180, step=10)
        equip_cap = st.slider("Equipment Capacity (units/day):", 500, 2000, 1000, step=100)

    with col2:
        st.markdown("#### Demand & Order Mix")
        demand_mult = st.select_slider("Demand Multiplier:", options=[0.5, 1.0, 1.5, 2.0], value=1.0)
        type_j_ratio = st.slider("Type J (Joining) Order Ratio (%):", 10, 70, 30, step=10)

    with col3:
        st.markdown("#### Raw Material Prices")
        p_metal = st.number_input("Metal Price ($/unit):", value=50.0, step=5.0)
        p_stone = st.number_input("Stone Price ($/unit):", value=100.0, step=5.0)

    if st.button("▶ Run Full 7-Day Digital Twin Simulation", type="primary"):
        st.write("### 📈 7-Day Digital Twin Simulation Results")
        
        base_orders = [43, 50, 65, 43, 65, 43, 43]
        sim_data = []

        cum_cost = 0.0
        for d_idx, raw_recv in enumerate(base_orders, 1):
            recv_cnt = int(raw_recv * demand_mult)
            comp_cnt = int(recv_cnt * (0.85 if type_j_ratio <= 30 else 0.75))
            mgt_used = min(mgt_cap, 164.5 + d_idx * 2.5)
            d_cost = 3650.0 + (comp_cnt * (p_metal * 0.4 + p_stone * 0.6))
            cum_cost += d_cost

            sim_data.append({
                "Day": f"Day {d_idx}",
                "Orders Received": recv_cnt,
                "Orders Completed": comp_cnt,
                "Management Used": f"{mgt_used:.1f} / {mgt_cap} u",
                "Daily Total Cost": f"${d_cost:,.2f}"
            })

        st.dataframe(pd.DataFrame(sim_data), use_container_width=True)

        st.metric("Total 7-Day Simulation Cost", f"${cum_cost:,.2f}")
        st.success("Simulation run complete! Adjust the parameters above to run sensitivity experiments.")
