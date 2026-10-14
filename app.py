import streamlit as st
import pulp
import pandas as pd
import json

st.set_page_config(
    page_title="Jewelry Supply Chain Teaching Tool",
    page_icon="💎",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.1rem; color: #94a3b8; margin-bottom: 1.2rem; }
    .card-box { background-color: #1e293b; padding: 1.2rem; border-radius: 0.5rem; border: 1px solid #334155; margin-bottom: 1rem; }
    .highlight-text { color: #38bdf8; font-weight: 600; }
    .score-good { color: #10b981; font-weight: bold; }
    .score-warn { color: #f59e0b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💎 Jewelry Supply Chain Teaching Tool</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive Operational Decision Game & Digital Twin Sandbox</div>', unsafe_allow_html=True)

# --- INTRODUCTORY SETUP & INSTRUCTIONS (BEFORE MODE SELECTION) ---
with st.expander("📚 **Factory Setup, Process Flow & Game Instructions (Read First)**", expanded=True):
    st.markdown("""
    ### 🏭 1. Factory Setup & Process Flow
    Welcome to the **Jewelry Supply Chain Simulator**. You are managing a fine jewelry manufacturing plant. Each customer order consists of 1 to 50 units and flows through sequential production stages:
    * **Optional Design Stage:** Takes **1 day** per order (batch level). Orders sent through Design incur a **$100 order fee** and have a **25% probability** of reducing metal requirement to 0.9 units/piece (otherwise 1.0 unit).
    * **Pre-Production Stage:** Requires 1 day per unit. Equipment capacity is capped at **1,000 units/day**.
    * **Post-Production Stage:** Finishing & assembly. Equipment capacity is capped at **1,000 units/day**.
    
    #### Order Types & Dwell Times:
    * **Type O (Ordinary Orders):** Takes **1 day in Pre-Production** and **1 day in Post-Production** (Total cycle: 2 days).
    * **Type J (Joining Orders):** Takes **1 day in Pre-Production** and **2 days in Post-Production** (Total cycle: 3 days).
    """)

    st.markdown("### 📊 2. Resource Constraints & Operating Rules")
    st.markdown("""
    Every product unit requires **1 unit of Metal ($50/unit)** and **1 unit of Stone ($100/unit)** as Raw Material Inputs.
    A mandatory **100-unit Raw Material Safety Floor** must be maintained at all times.
    
    Daily factory operations are bounded by 4 distinct classes of artisans and a overall **Management Resource Cap (Default: 180 units/day)**:
    """)

    # Constraints Table
    resource_df = pd.DataFrame([
        {
            "Artisan Class": "Regular Payroll",
            "Starting Staff (Pre / Post)": "60 / 70",
            "Max Capacity": "80 / 80",
            "Daily Output": "5 units/day",
            "Base Cost": "$10/day ($2.00/u)",
            "Overtime Rule": "Up to 0.5 day ($20/day)",
            "Allowed Orders": "Type O Only",
            "Management Cost": "0.4 units / artisan"
        },
        {
            "Artisan Class": "Skilled Payroll",
            "Starting Staff (Pre / Post)": "20 / 20",
            "Max Capacity": "20 / 25",
            "Daily Output": "5 units/day",
            "Base Cost": "$15/day ($3.00/u)",
            "Overtime Rule": "Up to 0.5 day ($30/day)",
            "Allowed Orders": "Type O & Type J",
            "Management Cost": "2.0 units / artisan"
        },
        {
            "Artisan Class": "Skilled Contractor",
            "Starting Staff (Pre / Post)": "10 / 15",
            "Max Capacity": "15 / 30",
            "Daily Output": "8 units/day",
            "Base Cost": "$30/day ($3.75/u)",
            "Overtime Rule": "None",
            "Allowed Orders": "Type O & Type J",
            "Management Cost": "1.0 unit / artisan"
        },
        {
            "Artisan Class": "Outsource Contractor",
            "Starting Staff (Pre / Post)": "10 / 15",
            "Max Capacity": "30 / 40",
            "Daily Output": "8 units/day",
            "Base Cost": "$40/day ($5.00/u)",
            "Overtime Rule": "None",
            "Allowed Orders": "Type O & Type J",
            "Management Cost": "0.3 units / artisan"
        }
    ])
    st.dataframe(resource_df, use_container_width=True)

    st.markdown("""
    ### 🎯 3. Objective of the Game
    Each day, new customer orders arrive with specified unit quantities and target delivery dates (5-day window for a 100% On-Time Delivery score). 
    As the Factory Operations Manager, you must decide at the end of each day:
    1. **Raw Material Procurement:** How many units of **Metal** and **Stone** to purchase for tomorrow's production.
    2. **Payroll Overtime:** How much overtime (0.0 to 0.5 days) to run for Regular Payroll artisans.
    3. **Contractor Recruitment:** How many **Skilled Contractors** or **Outsource Contractors** to recruit daily.

    Your primary goal is to **minimize total operational costs** while fulfilling orders on time and preventing raw material stockouts.

    ### ⚖️ 4. Mathematical LP Optimization Benchmark
    After submitting your decisions for each day, your choices will be evaluated against a **Linear Programming (LP) Mathematical Benchmark** solver operating under the exact same factory state.
    At the end of each turn, the system reveals the **exact optimal decision variable values** (optimal material purchases, optimal overtime, and optimal contractor recruitment) alongside your choices so you can analyze where and why your strategy diverged from the mathematical optimum!
    """)

st.divider()

# Mode Selection
mode = st.sidebar.radio(
    "Select Learning Mode:",
    ["🎮 Mode 1: Daily Decision Game (Player vs. LP)", "🔬 Mode 2: Digital Twin Sandbox"]
)

# Solver Helper for Daily LP Benchmark
def solve_daily_lp_benchmark(day_idx, req_metal, req_stone, mgt_cap=180.0):
    """
    Computes exact mathematical optimal decision variables for a given day.
    """
    prob = pulp.LpProblem("Daily_Optimal_Benchmark", pulp.LpMinimize)
    
    # Variables
    buy_metal = pulp.LpVariable("buy_metal", lowBound=0, cat=pulp.LpContinuous)
    buy_stone = pulp.LpVariable("buy_stone", lowBound=0, cat=pulp.LpContinuous)
    ot_reg = pulp.LpVariable("ot_reg", lowBound=0, upBound=30, cat=pulp.LpContinuous)
    hire_out = pulp.LpVariable("hire_out", lowBound=0, upBound=30, cat=pulp.LpInteger)
    
    # Management constraint
    prob += (164.5 + (ot_reg * 0.4) + (hire_out * 0.3) <= mgt_cap, "Mgt_Cap")
    
    # Material satisfaction
    prob += (buy_metal >= req_metal, "Metal_Req")
    prob += (buy_stone >= req_stone, "Stone_Req")
    
    # Objective: Minimize Daily Cost
    cost = 3650.0 + (buy_metal * 50.0) + (buy_stone * 100.0) + (ot_reg * 20.0) + (hire_out * 40.0)
    prob += cost
    
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    return {
        "opt_buy_metal": max(0.0, float(pulp.value(buy_metal) or 0.0)),
        "opt_buy_stone": max(0.0, float(pulp.value(buy_stone) or 0.0)),
        "opt_ot_reg": float(pulp.value(ot_reg) or 0.0),
        "opt_hire_out": float(pulp.value(hire_out) or 0.0),
        "opt_cost": float(pulp.value(prob.objective) or 3650.0)
    }

# --- MODE 1: DAILY INTERACTIVE DECISION GAME ---
if mode == "🎮 Mode 1: Daily Decision Game (Player vs. LP)":
    st.header("🎮 Mode 1: Daily Interactive Decision Game")

    if 'day' not in st.session_state:
        st.session_state.day = 1
        st.session_state.metal_stock = 500.0
        st.session_state.stone_stock = 500.0
        st.session_state.cum_player_cost = 0.0
        st.session_state.cum_lp_cost = 0.0
        st.session_state.game_history = []
        st.session_state.last_comparison = None

    st.subheader(f"📅 Current Simulation State: Day {st.session_state.day} of 7")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Metal Inventory", f"{st.session_state.metal_stock:.1f} units")
    m2.metric("Stone Inventory", f"{st.session_state.stone_stock:.1f} units")
    m3.metric("Safety Stock Floor", "100.0 units")
    m4.metric("Cumulative Player Cost", f"${st.session_state.cum_player_cost:,.2f}")

    day_orders_summary = {
        1: "43 Orders (500 units) — Opening Baseline Demand",
        2: "50 Orders (580 units) — +20% demand surge on small orders",
        3: "65 Orders (755 units) — +50% peak demand surge",
        4: "43 Orders (500 units) — Normal demand",
        5: "65 Orders (755 units) — +50% peak demand surge",
        6: "43 Orders (500 units) — Normal demand",
        7: "43 Orders (500 units) — Normal demand"
    }

    req_materials_by_day = { 1: (0, 0), 2: (180, 180), 3: (255, 255), 4: (100, 100), 5: (255, 255), 6: (100, 100), 7: (100, 100) }

    st.info(f"**📦 Today's Incoming Demand (Day {st.session_state.day}):** {day_orders_summary.get(st.session_state.day, 'Standard Demand')}")

    with st.form("daily_decision_form"):
        st.write("### 🛠️ Select Your Daily Decision Variables")
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

        # LP Benchmark Calculation for Today
        req_m, req_s = req_materials_by_day.get(st.session_state.day, (100, 100))
        lp_sol = solve_daily_lp_benchmark(st.session_state.day, req_m, req_s, 180.0)
        lp_day_cost = lp_sol['opt_cost']

        efficiency = min(100.0, (lp_day_cost / player_day_cost) * 100.0) if player_day_cost > 0 else 100.0

        st.session_state.cum_player_cost += player_day_cost
        st.session_state.cum_lp_cost += lp_day_cost

        # Record Comparison for student feedback
        st.session_state.last_comparison = {
            "day": st.session_state.day,
            "player_m": buy_m, "opt_m": lp_sol['opt_buy_metal'],
            "player_s": buy_s, "opt_s": lp_sol['opt_buy_stone'],
            "player_ot": ot_reg, "opt_ot": lp_sol['opt_ot_reg'],
            "player_out": hire_out, "opt_out": lp_sol['opt_hire_out'],
            "player_cost": player_day_cost, "opt_cost": lp_day_cost,
            "score": efficiency
        }

        st.session_state.game_history.append({
            "Day": f"Day {st.session_state.day}",
            "Player Cost": f"${player_day_cost:,.2f}",
            "LP Optimal Cost": f"${lp_day_cost:,.2f}",
            "Efficiency Score": f"{efficiency:.1f}%"
        })

        st.session_state.metal_stock = max(100.0, st.session_state.metal_stock + buy_m - 200.0)
        st.session_state.stone_stock = max(100.0, st.session_state.stone_stock + buy_s - 200.0)
        st.session_state.day += 1

        st.success("Day completed! Review your decision variable comparison below.")

    # Reveal Actual LP Decision Variables vs Player Decisions
    if st.session_state.last_comparison:
        st.write(f"### 🔍 Decision Variable Comparison (Day {st.session_state.last_comparison['day']})")
        st.markdown("Compare your choices against the **Linear Programming (LP) Mathematical Optimum**:")

        comp_data = pd.DataFrame([
            {
                "Decision Variable": "Metal Purchased (units)",
                "Your Choice": f"{st.session_state.last_comparison['player_m']:.0f} u",
                "LP Optimal Choice": f"{st.session_state.last_comparison['opt_m']:.0f} u",
                "Cost Difference": f"${(st.session_state.last_comparison['player_m'] - st.session_state.last_comparison['opt_m']) * 50:,.2f}"
            },
            {
                "Decision Variable": "Stone Purchased (units)",
                "Your Choice": f"{st.session_state.last_comparison['player_s']:.0f} u",
                "LP Optimal Choice": f"{st.session_state.last_comparison['opt_s']:.0f} u",
                "Cost Difference": f"${(st.session_state.last_comparison['player_s'] - st.session_state.last_comparison['opt_s']) * 100:,.2f}"
            },
            {
                "Decision Variable": "Regular Payroll Overtime (days)",
                "Your Choice": f"{st.session_state.last_comparison['player_ot']:.1f} days",
                "LP Optimal Choice": f"{st.session_state.last_comparison['opt_ot']:.1f} days",
                "Cost Difference": f"${(st.session_state.last_comparison['player_ot'] - st.session_state.last_comparison['opt_ot']) * 20:,.2f}"
            },
            {
                "Decision Variable": "Outsource Contractors Hired",
                "Your Choice": f"{st.session_state.last_comparison['player_out']:.0f} artisans",
                "LP Optimal Choice": f"{st.session_state.last_comparison['opt_out']:.0f} artisans",
                "Cost Difference": f"${(st.session_state.last_comparison['player_out'] - st.session_state.last_comparison['opt_out']) * 40:,.2f}"
            },
            {
                "Decision Variable": "TOTAL DAILY OPERATIONAL COST",
                "Your Choice": f"${st.session_state.last_comparison['player_cost']:,.2f}",
                "LP Optimal Choice": f"${st.session_state.last_comparison['opt_cost']:,.2f}",
                "Cost Difference": f"${(st.session_state.last_comparison['player_cost'] - st.session_state.last_comparison['opt_cost']):,.2f}"
            }
        ])
        st.dataframe(comp_data, use_container_width=True)

    if st.session_state.game_history:
        st.write("### 📊 Overall Session Scorecard History")
        st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)

    if st.button("🔄 Reset Game Session"):
        st.session_state.day = 1
        st.session_state.metal_stock = 500.0
        st.session_state.stone_stock = 500.0
        st.session_state.cum_player_cost = 0.0
        st.session_state.cum_lp_cost = 0.0
        st.session_state.game_history = []
        st.session_state.last_comparison = None
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
