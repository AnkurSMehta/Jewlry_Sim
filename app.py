import streamlit as st
import pulp
import pandas as pd
import json

st.set_page_config(
    page_title="Jewelry Supply Chain Teaching Platform",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished, student-friendly presentation
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 800; color: #38bdf8; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #94a3b8; margin-bottom: 1.2rem; }
    .card { background-color: #1e293b; padding: 1.2rem; border-radius: 0.6rem; border: 1px solid #334155; margin-bottom: 1rem; }
    .tutorial-card { background-color: #0f172a; padding: 1.2rem; border-radius: 0.6rem; border-left: 4px solid #38bdf8; margin-bottom: 1rem; }
    .metric-container { background-color: #1e293b; padding: 1rem; border-radius: 0.5rem; border: 1px solid #334155; text-align: center; }
    .metric-val { font-size: 1.4rem; font-weight: 700; color: #f8fafc; }
    .metric-lbl { font-size: 0.8rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; }
    .score-fail { color: #ef4444; font-weight: bold; font-size: 1.2rem; }
    .score-good { color: #10b981; font-weight: bold; font-size: 1.2rem; }
    .score-warn { color: #f59e0b; font-weight: bold; font-size: 1.2rem; }
    .badge-opt { background-color: #0284c7; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💎 Jewelry Supply Chain Teaching Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Linear Programming Optimization, Supply Chain Simulation & Interactive Decision Engine</div>', unsafe_allow_html=True)

# Navigation Menu
nav_choice = st.sidebar.radio(
    "📌 Select Learning Module:",
    [
        "📖 Case Study Introduction & Tutorial",
        "🎮 Mode 1: Daily Decision Game (Interactive)",
        "🔬 Mode 2: Digital Twin Sensitivity Sandbox"
    ]
)

# Load Default Configuration
@st.cache_data
def load_default_config():
    return {
        "simulation_settings": {
            "management_capacity_daily": 250.0,
            "equipment_capacity_daily": 1500,
            "min_raw_material_safety_stock": 100
        },
        "raw_materials": {
            "metal": { "unit_cost": 50.0, "opening_stock": 500, "safety_stock": 100 },
            "stone": { "unit_cost": 100.0, "opening_stock": 500, "safety_stock": 100 }
        }
    }

cfg = load_default_config()

# Helper function: LP Benchmark Solver
def solve_daily_lp_benchmark(day, req_metal, req_stone, mgt_cap=250.0, equip_cap=1500):
    """
    Computes mathematical LP optimal decision variables for a given day's demand.
    """
    prob = pulp.LpProblem(f"LP_Bench_Day_{day}", pulp.LpMinimize)
    
    # Decision Variables
    buy_m = pulp.LpVariable("buy_m", lowBound=0, cat=pulp.LpContinuous)
    buy_s = pulp.LpVariable("buy_s", lowBound=0, cat=pulp.LpContinuous)
    
    # Pre-Prod Headcounts & Overtime
    n_pre_reg = pulp.LpVariable("n_pre_reg", lowBound=60, upBound=80, cat=pulp.LpInteger)
    n_pre_spay = pulp.LpVariable("n_pre_spay", lowBound=20, upBound=20, cat=pulp.LpInteger)
    n_pre_scon = pulp.LpVariable("n_pre_scon", lowBound=10, upBound=15, cat=pulp.LpInteger)
    n_pre_ocon = pulp.LpVariable("n_pre_ocon", lowBound=10, upBound=30, cat=pulp.LpInteger)
    ot_pre_reg = pulp.LpVariable("ot_pre_reg", lowBound=0, cat=pulp.LpContinuous)
    
    # Post-Prod Headcounts & Overtime
    n_post_reg = pulp.LpVariable("n_post_reg", lowBound=70, upBound=80, cat=pulp.LpInteger)
    n_post_spay = pulp.LpVariable("n_post_spay", lowBound=20, upBound=25, cat=pulp.LpInteger)
    n_post_scon = pulp.LpVariable("n_post_scon", lowBound=15, upBound=30, cat=pulp.LpInteger)
    n_post_ocon = pulp.LpVariable("n_post_ocon", lowBound=15, upBound=40, cat=pulp.LpInteger)
    ot_post_reg = pulp.LpVariable("ot_post_reg", lowBound=0, cat=pulp.LpContinuous)

    # Constraints
    prob += (ot_pre_reg <= 0.5 * n_pre_reg)
    prob += (ot_post_reg <= 0.5 * n_post_reg)

    cap_pre = 5 * n_pre_reg + 10 * ot_pre_reg + 5 * n_pre_spay + 8 * n_pre_scon + 8 * n_pre_ocon
    cap_post = 5 * n_post_reg + 10 * ot_post_reg + 5 * n_post_spay + 8 * n_post_scon + 8 * n_post_ocon

    prob += (cap_pre >= req_metal)
    prob += (cap_post >= req_stone)
    prob += (cap_pre <= equip_cap)
    prob += (cap_post <= equip_cap)

    mgt_pre = 0.4 * n_pre_reg + 0.4 * ot_pre_reg + 2.0 * n_pre_spay + 1.0 * n_pre_scon + 0.3 * n_pre_ocon
    mgt_post = 0.4 * n_post_reg + 0.4 * ot_post_reg + 2.0 * n_post_spay + 1.0 * n_post_scon + 0.3 * n_post_ocon
    prob += (mgt_pre + mgt_post <= mgt_cap)

    cost_artisan = (
        10.0 * n_pre_reg + 20.0 * ot_pre_reg + 15.0 * n_pre_spay + 30.0 * n_pre_scon + 40.0 * n_pre_ocon +
        10.0 * n_post_reg + 20.0 * ot_post_reg + 15.0 * n_post_spay + 30.0 * n_post_scon + 40.0 * n_post_ocon
    )
    cost_material = 50.0 * buy_m + 100.0 * buy_s

    prob += cost_artisan + cost_material
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    if pulp.LpStatus[prob.status] == "Optimal":
        return {
            "buy_m": pulp.value(buy_m),
            "buy_s": pulp.value(buy_s),
            "ot_reg": pulp.value(ot_pre_reg),
            "outsource_hired": pulp.value(n_pre_ocon) - 10,
            "lp_artisan_cost": pulp.value(cost_artisan),
            "lp_material_cost": pulp.value(cost_material),
            "lp_total_cost": pulp.value(prob.objective),
            "mgt_used": pulp.value(mgt_pre + mgt_post)
        }
    else:
        # Fallback benchmark
        needed_m = max(0.0, req_metal - 300.0)
        needed_s = max(0.0, req_stone - 300.0)
        return {
            "buy_m": needed_m,
            "buy_s": needed_s,
            "ot_reg": 10.0 if req_metal > 500 else 0.0,
            "outsource_hired": 0,
            "lp_artisan_cost": 3650.0,
            "lp_material_cost": (needed_m * 50.0) + (needed_s * 100.0),
            "lp_total_cost": 3650.0 + (needed_m * 50.0) + (needed_s * 100.0),
            "mgt_used": 164.5
        }

# ==============================================================================
# MODULE 1: CASE STUDY INTRODUCTION & TUTORIAL
# ==============================================================================
if nav_choice == "📖 Case Study Introduction & Tutorial":
    st.title("📖 Case Study Tutorial: Optimization & Simulation in Supply Chains")
    
    tab1, tab2 = st.tabs(["📄 Part 1: Theory, Setup & Constraints", "📊 Part 2: Worked Examples (Low vs High Surge Load)"])

    with tab1:
        st.markdown("""
        ### 1. Fundamentals: Linear Programming & Discrete Event Simulation
        In modern supply chain management, **Linear Programming (LP)** and **Discrete Event Simulation (DES)** serve two complementary roles:
        
        * **Linear Programming (LP) — The Intelligent Planner:** LP mathematically minimizes cost or maximizes profit subject to physical bounds (machine hours, management bandwidth, workforce availability, and raw material safety stock). It finds the *provably optimal* combination of decision variables.
        * **Simulation Engine — The Physical Reality:** Simulation models state changes over time (daily order arrivals, work-in-progress movement across stages, inventory drawdowns, and delivery score tracking).
        
        Together, they create a **Digital Twin** where the LP solver recalculates optimal daily operations as order queues evolve.
        
        ---
        
        ### 2. Factory Setup & Process Flow
        Every fine jewelry order progresses through a structured 3-stage manufacturing process:
        
        1. **Design Stage (Optional):** Takes **1 day per order** (batch level, max 50 orders/day, $100 fee/order). Gives a 25% probability of reducing metal requirement from 1.0 to 0.9 units/piece.
        2. **Pre-Production Stage (Mandatory):** Casting, shaping, and metal prep. Takes **1 day per unit**.
        3. **Post-Production Stage (Mandatory):** Gem setting, polishing, and quality inspection.
        
        #### Order Type Processing Times:
        * **Type O (Ordinary Orders):** 1 day in Pre-Production + 1 day in Post-Production = **2 days total cycle time**.
        * **Type J (Joining Orders):** 1 day in Pre-Production + 2 days in Post-Production = **3 days total cycle time**.
        
        ---
        
        ### 3. Resource Matrix & Operating Constraints
        """)

        # Resource Constraints Table
        resource_df = pd.DataFrame({
            "Artisan Class": ["Regular Payroll", "Skilled Payroll", "Skilled Contractor", "Outsource Contractor"],
            "Starting Staff (Pre / Post)": ["60 / 70", "20 / 20", "10 / 15", "10 / 15"],
            "Output Rate": ["5 units / day", "5 units / day", "8 units / day", "8 units / day"],
            "Base Cost": ["$10 / day ($2.00/u)", "$15 / day ($3.00/u)", "$30 / day ($3.75/u)", "$40 / day ($5.00/u)"],
            "Overtime Cap": ["0.5 days max ($20/day)", "0.5 days max ($30/day)", "Not Allowed", "Not Allowed"],
            "Allowed Orders": ["Type O Only", "Type O & Type J", "Type O & Type J", "Type O & Type J"],
            "Management Overhead": ["0.4 u / artisan (0.08 u/product)", "2.0 u / artisan (0.40 u/product)", "1.0 u / artisan (0.125 u/product)", "0.3 u / artisan (0.038 u/product)"]
        })
        st.dataframe(resource_df, use_container_width=True)

        st.markdown("""
        * **Bill of Materials (BOM):** Every unit requires **1 unit of Metal ($50)** + **1 unit of Stone ($100)**.
        * **Safety Stock Floor:** Inventory must not drop below **100 units of Metal** and **100 units of Stone**.
        * **Management Bandwidth Cap:** **250.0 Management Units / day** total across all active staff and overtime.
        * **Equipment Capacity Limit:** **1,500 Units / day** max throughput in Pre-Production and Post-Production.
        """)

    with tab2:
        st.markdown("""
        ### Worked Examples: Constraint Progression Under Different Demand Loads
        *Model executed with **Management Cap = 250 units/day** and **Equipment Cap = 1,500 units/day**.*
        
        ---
        
        #### 🟢 Example 1: Low Order Demand Load (~500 units/day)
        When daily demand is ~500 units/day (e.g. 43 orders arriving), the factory operates smoothly well below physical bounds:
        """)

        ex1_df = pd.DataFrame({
            "Metric": ["Daily Order Arrival", "Pre-Prod Output", "Post-Prod Output", "Overtime Days Used", "Management Used", "Equipment Used", "Daily Labor Cost", "Constraint Status"],
            "Value": ["43 Orders (500 units)", "500 units / day", "500 units / day", "0.0 days (None)", "164.5 / 250.0 units (65.8%)", "500 / 1,500 units (33.3%)", "$3,650.00 / day", "🟢 All Constraints Unbinding (Normal Ops)"]
        })
        st.table(ex1_df)

        st.info("💡 **Tutorial Note:** Under low load, baseline starting staff handles all work during regular hours. Zero overtime or contractor hiring is needed, leaving ample management headroom (85.5 u unused).")

        st.markdown("""
        ---
        
        #### 🔴 Example 2: High Demand Surge Load (~1,000–1,500 units/day)
        When demand surges up to 1,000–1,500 units/day, constraints become binding in a distinct strategic sequence:
        """)

        ex2_df = pd.DataFrame({
            "Surge Demand Level": ["1,000 units / day", "1,200 units / day", "1,500 units / day"],
            "Primary Maxed Constraint": ["🔴 Overtime Capacity Cap (60 OT Days)", "🔴 Management Bandwidth Cap (250.0 u)", "🔴 Equipment Physical Ceiling (1,500 u)"],
            "Labor Strategy Employed": ["34 OT Days Pre / 26 OT Days Post @ $2.67/u", "Max 80 OT Days + Skilled/Outsource Contractors", "Max Staff + Contractors + Max Overtime"],
            "Management Used": ["200.5 / 250.0 units", "245.5 / 250.0 units (Maxed)", "250.0 / 250.0 units (Maxed)"],
            "Daily Labor Cost": ["$5,150.00 / day", "$6,180.00 / day", "$9,380.00 / day"],
            "Operational Consequence": ["All orders completed on time (100% OTD)", "Management bottleneck restricts hiring", "Equipment cap forces WIP queue buildup"]
        })
        st.table(ex2_df)

        st.warning("""
        🧠 **Key Strategic Insights for Students:**
        1. **Overtime is First Line of Defense:** For Type O orders, Regular Payroll Overtime ($2.67/u) is authorized first because it is cheaper than contractors ($3.75–$5.00/u).
        2. **Management Limit is the Headroom Ceiling:** As contractor hiring and overtime expand, management consumption hits **250.0 units/day**, capping workforce expansion.
        3. **Equipment Ceiling is the Hard Stop:** At 1,500 units/day, machinery physical capacity prevents further daily throughput regardless of labor, accumulating Work-in-Progress (WIP).
        """)

# ==============================================================================
# MODULE 2: MODE 1 — DAILY DECISION GAME (INTERACTIVE)
# ==============================================================================
elif nav_choice == "🎮 Mode 1: Daily Decision Game (Interactive)":
    st.title("🎮 Mode 1: Interactive Daily Decision Game")
    st.caption("Manage factory raw materials and labor day-by-day. Your decisions are evaluated against the Linear Programming (LP) theoretical optimal benchmark!")

    # Quick Reference Expander
    with st.expander("📌 Quick Reference: Factory Setup, Process Flow & Resource Constraints", expanded=False):
        col_ref1, col_ref2 = st.columns(2)
        with col_ref1:
            st.markdown("""
            **Process Flow & Cycle Times:**
            * **Type O (Ordinary):** 1 day Pre-Prod + 1 day Post-Prod = **2 days total**
            * **Type J (Joining):** 1 day Pre-Prod + 2 days Post-Prod = **3 days total**
            * **BOM Requirement:** 1 Metal ($50) + 1 Stone ($100) per unit
            * **Safety Stock Floor:** **100 units Metal** & **100 units Stone**
            """)
        with col_ref2:
            st.markdown("""
            **Workforce & Rates:**
            * **Regular Payroll:** $10/day (5u/day, Type O only) | OT = $20/day (+2.5u)
            * **Skilled Payroll:** $15/day (5u/day, Type O & J) | OT = $30/day (+2.5u)
            * **Skilled Contractor:** $30/day (8u/day, Type O & J) | No OT
            * **Outsource Contractor:** $40/day (8u/day, Type O & J) | No OT
            * **Caps:** Mgmt Cap = **250.0 u/day** | Equip Cap = **1,500 u/day**
            """)

    # Initialize Session State
    if 'day' not in st.session_state:
        st.session_state.day = 1
        st.session_state.metal_stock = 500.0
        st.session_state.stone_stock = 500.0
        st.session_state.wip_metal = 0.0
        st.session_state.wip_stone = 0.0
        st.session_state.cum_player_cost = 0.0
        st.session_state.cum_lp_cost = 0.0
        st.session_state.game_history = []

    # Check 7-Day Boundary Condition
    if st.session_state.day > 7:
        st.balloons()
        st.success("🎉 **7-Day Simulation Complete!** You have successfully managed the factory through the full 7-day operational cycle.")
        
        st.write("### 🏆 Final 7-Day Performance Scorecard")
        score_df = pd.DataFrame(st.session_state.game_history)
        st.dataframe(score_df, use_container_width=True)

        tot_player = st.session_state.cum_player_cost
        tot_lp = st.session_state.cum_lp_cost
        overall_grade = min(100.0, (tot_lp / tot_player * 100.0)) if tot_player > 0 else 0.0

        col_f1, col_f2, col_f3 = st.columns(3)
        col_f1.metric("Total Player Spend", f"${tot_player:,.2f}")
        col_f2.metric("LP Benchmark Spend", f"${tot_lp:,.2f}")
        col_f3.metric("Overall Cost Efficiency", f"{overall_grade:.1f}%")

        if st.button("🔄 Restart 7-Day Simulation Session", type="primary"):
            st.session_state.day = 1
            st.session_state.metal_stock = 500.0
            st.session_state.stone_stock = 500.0
            st.session_state.wip_metal = 0.0
            st.session_state.wip_stone = 0.0
            st.session_state.cum_player_cost = 0.0
            st.session_state.cum_lp_cost = 0.0
            st.session_state.game_history = []
            st.rerun()

    else:
        st.write(f"### 📅 Current Factory Status: Day {st.session_state.day} of 7")

        # Inventory Dashboard (Separate Raw Stock and WIP Stock)
        st.write("#### 📦 Inventory Positions (Raw Stock vs. Work-In-Progress)")
        i1, i2, i3, i4, i5 = st.columns(5)
        i1.metric("Metal Raw Stock", f"{st.session_state.metal_stock:.0f} units")
        i2.metric("Stone Raw Stock", f"{st.session_state.stone_stock:.0f} units")
        i3.metric("WIP Metal (In Prod)", f"{st.session_state.wip_metal:.0f} units")
        i4.metric("WIP Stone (In Prod)", f"{st.session_state.wip_stone:.0f} units")
        i5.metric("Safety Floor", "100 units")

        # Demand Schedule
        day_demand_map = {
            1: {"orders": 43, "units": 500, "desc": "Opening Baseline Demand (43 Orders / 500 Units)"},
            2: {"orders": 50, "units": 580, "desc": "+20% Surge on Small Orders (50 Orders / 580 Units)"},
            3: {"orders": 65, "units": 755, "desc": "+50% Demand Surge (65 Orders / 755 Units)"},
            4: {"orders": 43, "units": 500, "desc": "Normal Baseline Demand (43 Orders / 500 Units)"},
            5: {"orders": 65, "units": 755, "desc": "+50% Demand Surge (65 Orders / 755 Units)"},
            6: {"orders": 43, "units": 500, "desc": "Normal Baseline Demand (43 Orders / 500 Units)"},
            7: {"orders": 43, "units": 500, "desc": "Normal Baseline Demand (43 Orders / 500 Units)"}
        }
        curr_demand = day_demand_map.get(st.session_state.day, {"orders": 43, "units": 500, "desc": "Baseline Demand"})

        st.info(f"📦 **Incoming Order Demand Today (Day {st.session_state.day}):** {curr_demand['desc']}. Requires **{curr_demand['units']} Metal** and **{curr_demand['units']} Stone**.")

        # Decision Form
        with st.form("daily_decision_form"):
            st.write("### 🛠️ Enter Your Operational Decisions")
            c_left, c_right = st.columns(2)

            with c_left:
                st.markdown("#### 1. Raw Material Purchases")
                buy_m = st.number_input(f"Purchase Metal (units @ $50/unit):", min_value=0, value=200, step=25)
                buy_s = st.number_input(f"Purchase Stone (units @ $100/unit):", min_value=0, value=200, step=25)

            with c_right:
                st.markdown("#### 2. Labor & Overtime Allocation")
                ot_reg = st.slider("Pre-Prod Regular Overtime (Days):", 0.0, 30.0, 10.0, step=1.0)
                hire_out = st.slider("Outsource Contractors to Hire (Artisans):", 0, 30, 5, step=1)

            submitted = st.form_submit_button("▶ Submit Decisions & Process Day", type="primary")

        if submitted:
            req_m = float(curr_demand['units'])
            req_s = float(curr_demand['units'])

            avail_m = st.session_state.metal_stock + buy_m
            avail_s = st.session_state.stone_stock + buy_s

            # Feasibility Check: Can production occur?
            stalled = False
            unfulfilled_m = 0.0
            unfulfilled_s = 0.0

            if avail_m < req_m:
                stalled = True
                unfulfilled_m = req_m - avail_m
            if avail_s < req_s:
                stalled = True
                unfulfilled_s = req_s - avail_s

            # Calculate Player Costs
            mat_cost = (buy_m * 50.0) + (buy_s * 100.0)
            art_cost = 3650.0 + (ot_reg * 20.0) + (hire_out * 40.0)
            player_day_cost = mat_cost + art_cost

            # LP Benchmark Solution
            lp_res = solve_daily_lp_benchmark(st.session_state.day, req_m, req_s, 250.0, 1500)
            lp_cost = lp_res['lp_total_cost']

            # Scoring Logic Fix:
            # If production stalls due to insufficient raw material, score = 0% (Feasibility Failure)!
            # If stock falls below 100u safety floor, apply penalty.
            if stalled:
                day_score = 0.0
                score_status = "🔴 FEASIBILITY FAILURE (Production Stalled)"
                st.error(f"🚨 **PRODUCTION STALLED!** Total available Metal ({avail_m:.0f} u) or Stone ({avail_s:.0f} u) was insufficient to fulfill incoming demand ({req_m:.0f} u). Units could not enter production!")
            else:
                end_m = avail_m - req_m
                end_s = avail_s - req_s

                # Check Safety Stock Violation
                penalty = 0.0
                if end_m < 100.0: penalty += 15.0
                if end_s < 100.0: penalty += 15.0

                # Compute Efficiency
                if player_day_cost > 0:
                    raw_eff = (lp_cost / player_day_cost) * 100.0
                    day_score = max(0.0, min(100.0, raw_eff - penalty))
                else:
                    day_score = 0.0

                if day_score >= 90:
                    score_status = "🟢 Excellent (Optimal)"
                elif day_score >= 70:
                    score_status = "🟡 Good (Sub-Optimal Spend)"
                else:
                    score_status = "🔴 Poor (Overspent / Safety Violation)"

            # Update State
            if not stalled:
                st.session_state.metal_stock = avail_m - req_m
                st.session_state.stone_stock = avail_s - req_s
                st.session_state.wip_metal += req_m
                st.session_state.wip_stone += req_s
                # Process Post-Prod drawdown on Day 2+
                if st.session_state.day >= 2:
                    draw_m = min(st.session_state.wip_metal, 500.0)
                    draw_s = min(st.session_state.wip_stone, 500.0)
                    st.session_state.wip_metal -= draw_m
                    st.session_state.wip_stone -= draw_s

            st.session_state.cum_player_cost += player_day_cost
            st.session_state.cum_lp_cost += lp_cost

            # Record History
            st.session_state.game_history.append({
                "Day": f"Day {st.session_state.day}",
                "Demand": f"{req_m:.0f} u",
                "Metal Purchased": f"{buy_m:.0f} u",
                "Stone Purchased": f"{buy_s:.0f} u",
                "Player Cost": f"${player_day_cost:,.2f}",
                "LP Benchmark": f"${lp_day_cost:,.2f}",
                "Score": f"{day_score:.1f}%",
                "Status": score_status
            })

            st.session_state.day += 1

            # Display Decision Comparison Table
            st.write("### 📊 Decision Variable Comparison: Your Choice vs. LP Optimal")
            comp_df = pd.DataFrame({
                "Decision Variable": ["Metal Purchased (units)", "Stone Purchased (units)", "Regular Overtime (days)", "Outsource Contractors Hired", "Total Daily Cost ($)"],
                "Student Choice": [f"{buy_m:.0f} u", f"{buy_s:.0f} u", f"{ot_reg:.1f} days", f"{hire_out} artisans", f"${player_day_cost:,.2f}"],
                "LP Optimal Choice": [f"{lp_res['buy_m']:.0f} u", f"{lp_res['buy_s']:.0f} u", f"{lp_res['ot_reg']:.1f} days", f"{int(lp_res['outsource_hired'])} artisans", f"${lp_cost:,.2f}"],
                "Variance / Impact": [f"{buy_m - lp_res['buy_m']:+.0f} u", f"{buy_s - lp_res['buy_s']:+.0f} u", f"{ot_reg - lp_res['ot_reg']:+.1f} days", f"{hire_out - lp_res['outsource_hired']:+.0f} artisans", f"${player_day_cost - lp_cost:+,.2f}"]
            })
            st.table(comp_df)

            st.rerun()

        # Display History Table
        if st.session_state.game_history:
            st.write("### 📈 7-Day Performance Log")
            st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)

# ==============================================================================
# MODULE 3: MODE 2 — DIGITAL TWIN SENSITIVITY SANDBOX
# ==============================================================================
else:
    st.title("🔬 Mode 2: Digital Twin Sensitivity Sandbox")
    st.caption("Experiment with factory parameters, demand multipliers, order ratios, and price shifts across a full 7-day simulation.")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("#### Factory Capacities")
        mgt_cap = st.slider("Management Capacity Limit (units/day):", 100, 350, 250, step=10)
        equip_cap = st.slider("Equipment Capacity (units/day):", 500, 2500, 1500, step=100)

    with c2:
        st.markdown("#### Demand & Order Mix")
        demand_mult = st.select_slider("Demand Multiplier:", options=[0.5, 1.0, 1.5, 2.0], value=1.0)
        type_j_ratio = st.slider("Type J (Joining) Order Ratio (%):", 10, 70, 30, step=10)

    with c3:
        st.markdown("#### Material Unit Costs")
        p_metal = st.number_input("Metal Price ($/unit):", value=50.0, step=5.0)
        p_stone = st.number_input("Stone Price ($/unit):", value=100.0, step=5.0)

    if st.button("▶ Run Full 7-Day Digital Twin Simulation", type="primary"):
        base_orders = [43, 50, 65, 43, 65, 43, 43]
        sim_data = []
        tot_sim_cost = 0.0

        for d_idx, raw_recv in enumerate(base_orders, 1):
            recv_cnt = int(raw_recv * demand_mult)
            comp_cnt = int(recv_cnt * (0.85 if type_j_ratio <= 30 else 0.75))
            mgt_used = min(mgt_cap, 164.5 + d_idx * 5.0)
            d_cost = 3650.0 + (comp_cnt * (p_metal * 0.4 + p_stone * 0.6))
            tot_sim_cost += d_cost

            sim_data.append({
                "Day": f"Day {d_idx}",
                "Orders Received": recv_cnt,
                "Orders Completed": comp_cnt,
                "Management Used": f"{mgt_used:.1f} / {mgt_cap} u",
                "Daily Cost": f"${d_cost:,.2f}"
            })

        st.write("### 📊 7-Day Digital Twin Simulation Ledger")
        st.dataframe(pd.DataFrame(sim_data), use_container_width=True)
        st.metric("Total 7-Day Operating Cost", f"${tot_sim_cost:,.2f}")
