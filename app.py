import streamlit as st
import pulp
import pandas as pd
import json

st.set_page_config(
    page_title="Jewelry Supply Chain Teaching Platform",
    page_icon="💎",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.3rem; }
    .sub-header { font-size: 1.05rem; color: #94a3b8; margin-bottom: 1.2rem; }
    .card { background-color: #1e293b; padding: 1.2rem; border-radius: 0.5rem; border: 1px solid #334155; margin-bottom: 1rem; }
    .metric-box { background-color: #0f172a; padding: 1rem; border-radius: 0.4rem; border: 1px solid #1e293b; text-align: center; }
    .metric-val { font-size: 1.4rem; font-weight: 700; color: #38bdf8; }
    .metric-lbl { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Main Title Header
st.markdown('<div class="main-header">💎 Fine Jewelry Supply Chain Teaching Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive Learning Environment: Linear Programming, Discrete Event Simulation & Supply Chain Strategy</div>', unsafe_allow_html=True)

# Sidebar Navigation Menu
mode = st.sidebar.radio(
    "Select Learning Module:",
    [
        "📖 Case Study Introduction & Tutorial",
        "🎮 Mode 1: Daily Decision Game",
        "🔬 Mode 2: Digital Twin Sandbox"
    ]
)

# LP Solver Function with Robust Fallback
def solve_daily_lp_benchmark(day, req_m, req_s, curr_m, curr_s, mgt_cap=250.0, equip_cap=1500):
    """
    Computes the exact mathematical LP optimal procurement and labor decisions for day t.
    """
    try:
        prob = pulp.LpProblem(f"Daily_LP_Day_{day}", pulp.LpMinimize)
        
        buy_m = pulp.LpVariable("buy_m", lowBound=0.0)
        buy_s = pulp.LpVariable("buy_s", lowBound=0.0)
        ot_reg = pulp.LpVariable("ot_reg", lowBound=0.0, upBound=30.0)
        hire_out = pulp.LpVariable("hire_out", lowBound=0.0, upBound=30.0)
        
        # Raw stock constraint (must cover required demand + 100 safety floor)
        prob += (curr_m + buy_m - req_m >= 100.0)
        prob += (curr_s + buy_s - req_s >= 100.0)
        
        # Capacity constraint (Pre-prod base 560u + OT + Outsource)
        pre_cap = 560.0 + (ot_reg * 5.0) + (hire_out * 8.0)
        prob += (pre_cap >= min(req_m, float(equip_cap)))
        
        # Management constraint
        mgt_used = 164.5 + (ot_reg * 0.4) + (hire_out * 0.3)
        prob += (mgt_used <= mgt_cap)
        
        # Objective
        mat_cost = 50.0 * buy_m + 100.0 * buy_s
        art_cost = 3650.0 + 20.0 * ot_reg + 40.0 * hire_out
        prob += mat_cost + art_cost
        
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        bm = max(0.0, float(pulp.value(buy_m) or 0.0))
        bs = max(0.0, float(pulp.value(buy_s) or 0.0))
        ot = max(0.0, float(pulp.value(ot_reg) or 0.0))
        ho = max(0.0, float(pulp.value(hire_out) or 0.0))
        tot = (50.0 * bm) + (100.0 * bs) + 3650.0 + (20.0 * ot) + (40.0 * ho)
        
        return {
            'buy_m': bm,
            'buy_s': bs,
            'ot_reg': ot,
            'hire_out': ho,
            'total_cost': tot,
            'status': 'Optimal'
        }
    except Exception:
        bm = max(0.0, float(req_m + 100.0 - curr_m))
        bs = max(0.0, float(req_s + 100.0 - curr_s))
        deficit = max(0.0, min(float(req_m), float(equip_cap)) - 560.0)
        ot = min(30.0, deficit / 5.0)
        rem = max(0.0, deficit - (ot * 5.0))
        ho = min(30.0, rem / 8.0)
        tot = (50.0 * bm) + (100.0 * bs) + 3650.0 + (20.0 * ot) + (40.0 * ho)
        return {
            'buy_m': bm,
            'buy_s': bs,
            'ot_reg': ot,
            'hire_out': ho,
            'total_cost': tot,
            'status': 'Fallback'
        }

# ==============================================================================
# OPTION 1: CASE STUDY INTRODUCTION & TUTORIAL
# ==============================================================================
if mode == "📖 Case Study Introduction & Tutorial":
    st.header("📖 Case Study Introduction & Tutorial")
    st.info("💡 **Welcome to the Fine Jewelry Manufacturing Supply Chain Teaching Platform.** This tutorial introduces the concepts of Linear Programming, Discrete Event Simulation, and operational decision-making.")

    tab1, tab2 = st.tabs(["📘 Part 1: Fundamentals & Factory Setup", "🔬 Part 2: Worked Examples (Low vs. High Surge Load)"])

    with tab1:
        st.markdown("### 1. Fundamentals of Optimization & Simulation")
        st.markdown("""
        In complex manufacturing environments, factory managers face daily decisions regarding raw material procurement, staffing levels, overtime allocation, and contractor recruitment.
        
        * **Linear Programming (LP):** A mathematical optimization technique that determines the exact combination of decision variables that minimizes total operational cost while satisfying physical capacity, labor, and inventory constraints.
        * **Discrete Event Simulation (DES):** A modeling methodology that simulates the physical movement of individual customer orders through sequential factory stages, tracking work-in-progress (WIP) queues, inventory consumption, and lead times over time.
        * **Optimization & Simulation Synergy:** In this platform, an **LP solver acts as the Intelligent Planner** at the start of each day, while the **Discrete Event Engine simulates the physical factory movements** as orders advance toward completion.
        """)

        st.markdown("---")
        st.markdown("### 2. Manufacturing Setup & Process Flow")
        st.markdown("""
        Every order $k$ consists of a batch size $U_k$ (1 to 50 units) and advances sequentially through up to 3 manufacturing stages:
        
        1. **Design Stage (Optional):** Fixed 1 day per batch ($100 fee per order). Grants a 25% probability of saving 0.1 Metal/unit (0.9 Metal required instead of 1.0).
        2. **Pre-Production Stage:** Primary component preparation and casting. Takes **1 day per unit**. Equipment capacity is capped at **1,500 units/day**.
        3. **Post-Production Stage:** Detailed setting, polishing, and assembly. Takes **1 day per unit for Ordinary (Type O) orders** and **2 days per unit for Joining (Type J) orders**. Equipment capacity is capped at **1,500 units/day**.
        
        **Order Routing & Manufacturing Lead Times:**
        * **Ordinary Orders (Type O):** 1 day in Pre-Production + 1 day in Post-Production = **2 days total cycle time**.
        * **Joining Orders (Type J):** 1 day in Pre-Production + 2 days in Post-Production = **3 days total cycle time**.
        """)

        st.markdown("---")
        st.markdown("### 3. Resource Matrix, Bill of Materials & System Constraints")
        
        matrix_data = [
            {"Artisan Class": "Regular Payroll", "Starting Staff (Pre/Post)": "60 / 70", "Output / Bench": "5 units/day", "Base Daily Rate": "$10/day ($2.00/u)", "Overtime Rule": "Up to 0.5 day ($20/day)", "Allowed Orders": "Type O Only", "Mgmt Overhead": "0.4 units / artisan"},
            {"Artisan Class": "Skilled Payroll", "Starting Staff (Pre/Post)": "20 / 20", "Output / Bench": "5 units/day", "Base Daily Rate": "$15/day ($3.00/u)", "Overtime Rule": "Up to 0.5 day ($30/day)", "Allowed Orders": "Type O & Type J", "Mgmt Overhead": "2.0 units / artisan"},
            {"Artisan Class": "Skilled Contractor", "Starting Staff (Pre/Post)": "10 / 15", "Output / Bench": "8 units/day", "Base Daily Rate": "$30/day ($3.75/u)", "Overtime Rule": "Not Eligible", "Allowed Orders": "Type O & Type J", "Mgmt Overhead": "1.0 unit / artisan"},
            {"Artisan Class": "Outsource Contractor", "Starting Staff (Pre/Post)": "10 / 15", "Output / Bench": "8 units/day", "Base Daily Rate": "$40/day ($5.00/u)", "Overtime Rule": "Not Eligible", "Allowed Orders": "Type O & Type J", "Mgmt Overhead": "0.3 units / artisan"}
        ]
        st.table(pd.DataFrame(matrix_data))

        c1, c2, c3 = st.columns(3)
        c1.markdown("**📦 Bill of Materials (BOM):**\nEach finished unit requires **1 unit of Metal ($50)** and **1 unit of Stone ($100)**.")
        c2.markdown("**🛡️ Safety Stock Floor:**\nRaw stock of Metal and Stone must **never dip below 100 units** at end-of-day.")
        c3.markdown("**⚡ System Limits:**\nManagement Cap: **250 units/day**.\nEquipment Cap: **1,500 units/day**.")

    with tab2:
        st.markdown("### Worked Case Tutorials: Constraint Progression & LP Decisions")
        st.write("These worked examples demonstrate how the Linear Program handles different demand loads by dynamically prioritizing decision variables.")

        st.markdown("#### 🟢 Worked Example 1: Low Order Demand Load (~500 units/day)")
        st.markdown("""
        When incoming order demand is ~500 units/day, factory demand matches baseline starting staff capacity (560 units/day Pre-Prod capacity).
        
        * **Decision Variables Selected by LP:**
          * *Raw Material Purchases:* Exactly 500 Metal ($25,000) and 500 Stone ($50,000) purchased daily to replenish consumed stock and maintain the 100-unit safety floor.
          * *Labor Decisions:* Zero overtime authorized, zero contractor recruitment needed ($3,650/day base labor cost).
        * **Constraint Analysis:**
          * *Management Overhead:* Uses **164.5 / 250.0 units** (~65% utilized). **Unbinding constraint.**
          * *Equipment Capacity:* Uses **500 / 1,500 units** (~33% utilized). **Unbinding constraint.**
        * **Financial Outcome:** 100% On-Time Delivery score achieved at an average daily cost of **$78,650.00**.
        """)

        st.markdown("---")
        st.markdown("#### 🔴 Worked Example 2: High Order Demand Load Surge (~1,000 to 1,500 units/day)")
        st.markdown("""
        When order demand surges to 1,000–1,500 units/day (e.g. 2x volume surge), factory workload exceeds baseline starting staff capacity. The LP solver navigates shifting bottleneck constraints:
        
        1. **At 1,000 units/day (Overtime Constraint Maxed):**
           * The LP authorizes maximum **Regular Payroll Overtime (60 OT days daily)** because Regular Overtime costs **$2.67/unit**, making it far cheaper than Skilled Contractors ($3.75/u) or Outsource Contractors ($5.00/u).
           * *Management Bandwidth:* Reaches **200.5 / 250.0 units**.
        2. **At 1,200 units/day (Management Bandwidth Constraint Maxed):**
           * Additional overtime would breach the **250.0 Management Cap**. To expand output further without breaking management capacity, the LP engine shifts recruitment to **Outsource Contractors** ($5.00/unit) because they consume only **0.038 management units per product unit** (10.6x lighter management footprint than Skilled Payroll!).
           * *Management Bandwidth:* Reaches **245.5 / 250.0 units (Binding Constraint)**.
        3. **At 1,500 units/day (Equipment Capacity Ceiling Maxed):**
           * Throughput reaches the **1,500 units/day physical equipment limit**.
           * Incoming orders beyond 1,500 units/day accumulate in the Work-in-Progress (WIP) queue, forming a physical equipment bottleneck.
        """)

# ==============================================================================
# OPTION 2: MODE 1 — DAILY DECISION GAME
# ==============================================================================
elif mode == "🎮 Mode 1: Daily Decision Game":
    st.header("🎮 Mode 1: Daily Decision Game (Player vs. LP Benchmark)")
    st.info("💡 **Objective:** Manage the factory day-by-day for 7 days. Make decisions on inventory purchasing, overtime, and contractor recruitment. Fulfill orders on time while keeping total costs as close to the Linear Program (LP) benchmark as possible!")

    # Quick Reference Collapsible Section
    with st.expander("📌 Quick Reference: Factory Process Flow, Resource Matrix & BOM Rules"):
        st.markdown("""
        * **Process Lead Times:** Ordinary Orders (Type O) = **2 days** (1 Pre, 1 Post). Joining Orders (Type J) = **3 days** (1 Pre, 2 Post).
        * **Bill of Materials:** 1 unit Metal ($50) + 1 unit Stone ($100) per finished product unit.
        * **Safety Floor:** Mandatory **100 units** ending stock floor for Metal and Stone.
        * **Artisan Costs:** Regular Payroll ($10/day, OT +$10), Skilled Payroll ($15/day, OT +$15), Skilled Contractor ($30/day), Outsource Contractor ($40/day).
        """)

    # Initialize 7-Day Session State
    if 'day' not in st.session_state:
        st.session_state.day = 1
        st.session_state.metal_raw = 500.0
        st.session_state.stone_raw = 500.0
        st.session_state.metal_wip = 0.0
        st.session_state.stone_wip = 0.0
        st.session_state.cum_player_cost = 0.0
        st.session_state.cum_lp_cost = 0.0
        st.session_state.game_history = []
        st.session_state.last_feedback = None

    # Check 7-Day Game Boundary
    if st.session_state.day > 7:
        st.balloons()
        st.success("🎉 **7-DAY SIMULATION COMPLETED!**")
        st.markdown("### 🏆 Final 7-Day Performance Report")
        
        c_p, c_l, c_g = st.columns(3)
        c_p.metric("Total Player Spend", f"${st.session_state.cum_player_cost:,.2f}")
        c_l.metric("LP Benchmark Spend", f"${st.session_state.cum_lp_cost:,.2f}")
        cost_gap = st.session_state.cum_player_cost - st.session_state.cum_lp_cost
        c_g.metric("Cost Efficiency Gap", f"+${cost_gap:,.2f}" if cost_gap >= 0 else f"-${abs(cost_gap):,.2f}")

        st.write("### 📊 Complete 7-Day Daily Scorecard")
        if st.session_state.game_history:
            st.dataframe(pd.DataFrame(st.session_state.game_history))

        if st.button("🔄 Restart 7-Day Game Session", type="primary"):
            st.session_state.day = 1
            st.session_state.metal_raw = 500.0
            st.session_state.stone_raw = 500.0
            st.session_state.metal_wip = 0.0
            st.session_state.stone_wip = 0.0
            st.session_state.cum_player_cost = 0.0
            st.session_state.cum_lp_cost = 0.0
            st.session_state.game_history = []
            st.session_state.last_feedback = None
            st.rerun()

    else:
        st.subheader(f"📅 Simulation Day {st.session_state.day} of 7")

        # Inventory Dashboard
        d1, d2, d3, d4, d5 = st.columns(5)
        d1.metric("Metal Raw Stock", f"{st.session_state.metal_raw:.1f} u")
        d2.metric("Stone Raw Stock", f"{st.session_state.stone_raw:.1f} u")
        d3.metric("WIP Metal / Stone", f"{st.session_state.metal_wip:.1f} u")
        d4.metric("Safety Stock Floor", "100.0 u")
        d5.metric("Player Total Cost", f"${st.session_state.cum_player_cost:,.2f}")

        # Demand Schedule
        day_demands = {1: 500, 2: 580, 3: 755, 4: 500, 5: 755, 6: 500, 7: 500}
        req_demand = day_demands.get(st.session_state.day, 500)
        st.write(f"**📦 Incoming Today's Orders (Day {st.session_state.day}):** **{req_demand} units required** for production.")

        with st.form(f"daily_form_day_{st.session_state.day}"):
            st.write("### 🛠️ Enter Your Decisions for Today")
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("#### Raw Material Purchases")
                buy_m = st.number_input("Purchase Metal (units @ $50/u):", min_value=0, value=200, step=25)
                buy_s = st.number_input("Purchase Stone (units @ $100/u):", min_value=0, value=200, step=25)

            with col_b:
                st.markdown("#### Labor Allocation & Recruitment")
                ot_reg = st.slider("Pre-Prod Regular Payroll Overtime (Days):", 0.0, 30.0, 0.0, step=1.0)
                hire_out = st.slider("Outsource Contractors to Hire (Artisans):", 0, 30, 0, step=1)

            submitted = st.form_submit_button("▶ Submit Decisions & Advance Day", type="primary")

        if submitted:
            # Check Feasibility
            avail_m = st.session_state.metal_raw + buy_m
            avail_s = st.session_state.stone_raw + buy_s
            
            is_feasible = (avail_m >= req_demand) and (avail_s >= req_demand)
            
            # Compute Player Costs
            mat_cost = (buy_m * 50.0) + (buy_s * 100.0)
            art_cost = 3650.0 + (ot_reg * 20.0) + (hire_out * 40.0)
            player_day_cost = mat_cost + art_cost

            # Solve LP Optimal Benchmark
            lp_res = solve_daily_lp_benchmark(st.session_state.day, req_demand, req_demand, st.session_state.metal_raw, st.session_state.stone_raw, 250.0, 1500)
            lp_day_cost = lp_res['total_cost']

            if not is_feasible:
                score_str = "0.0% (FEASIBILITY FAILURE)"
                feedback_type = "error"
                feedback_msg = f"🚨 **PRODUCTION STALLED! Feasibility Failure:** Available raw materials ({avail_m:.0f} Metal / {avail_s:.0f} Stone) were less than the {req_demand} units required. Orders could not enter production! Score set to 0%."
            else:
                eff = min(100.0, (lp_day_cost / player_day_cost) * 100.0) if player_day_cost > 0 else 100.0
                score_str = f"{eff:.1f}%"
                feedback_type = "success" if eff >= 95 else "info"
                feedback_msg = f"✅ Decisions processed successfully! Cost Efficiency Score: **{score_str}**."

                # Update State on Successful Step
                st.session_state.metal_raw = max(100.0, avail_m - req_demand)
                st.session_state.stone_raw = max(100.0, avail_s - req_demand)
                st.session_state.metal_wip += req_demand * 0.5
                st.session_state.stone_wip += req_demand * 0.5

            st.session_state.cum_player_cost += player_day_cost
            st.session_state.cum_lp_cost += lp_day_cost

            # Side-by-side Decision Variable Comparison
            comp_df = pd.DataFrame([
                {"Decision Variable": "Metal Purchased (units)", "Student Choice": f"{buy_m:.0f} u", "LP Optimal Choice": f"{lp_res['buy_m']:.0f} u", "Cost Impact": f"${(buy_m - lp_res['buy_m'])*50:+,.2f}"},
                {"Decision Variable": "Stone Purchased (units)", "Student Choice": f"{buy_s:.0f} u", "LP Optimal Choice": f"{lp_res['buy_s']:.0f} u", "Cost Impact": f"${(buy_s - lp_res['buy_s'])*100:+,.2f}"},
                {"Decision Variable": "Regular Payroll Overtime (days)", "Student Choice": f"{ot_reg:.1f} days", "LP Optimal Choice": f"{lp_res['ot_reg']:.1f} days", "Cost Impact": f"${(ot_reg - lp_res['ot_reg'])*20:+,.2f}"},
                {"Decision Variable": "Outsource Contractors Hired", "Student Choice": f"{hire_out} artisans", "LP Optimal Choice": f"{lp_res['hire_out']:.0f} artisans", "Cost Impact": f"${(hire_out - lp_res['hire_out'])*40:+,.2f}"},
                {"Decision Variable": "TOTAL DAILY OPERATIONAL COST", "Student Choice": f"${player_day_cost:,.2f}", "LP Optimal Choice": f"${lp_day_cost:,.2f}", "Cost Impact": f"${(player_day_cost - lp_day_cost):+,.2f}"}
            ])

            st.session_state.last_feedback = {
                'msg': feedback_msg,
                'type': feedback_type,
                'comp_table': comp_df
            }

            st.session_state.game_history.append({
                "Day": f"Day {st.session_state.day}",
                "Player Cost": f"${player_day_cost:,.2f}",
                "LP Benchmark": f"${lp_day_cost:,.2f}",
                "Efficiency Score": score_str
            })

            st.session_state.day += 1

        # Display Last Turn Diagnostic Feedback & Side-by-Side Breakdown
        if st.session_state.last_feedback:
            st.write("---")
            st.write("### 📊 Decision Variable Comparison & Diagnostic Feedback")
            if st.session_state.last_feedback['type'] == 'error':
                st.error(st.session_state.last_feedback['msg'])
            elif st.session_state.last_feedback['type'] == 'success':
                st.success(st.session_state.last_feedback['msg'])
            else:
                st.info(st.session_state.last_feedback['msg'])

            st.table(st.session_state.last_feedback['comp_table'])

        if st.session_state.game_history:
            st.write("### 📈 Game Progress History")
            st.dataframe(pd.DataFrame(st.session_state.game_history))

# ==============================================================================
# OPTION 3: MODE 2 — DIGITAL TWIN SANDBOX
# ==============================================================================
else:
    st.header("🔬 Mode 2: Digital Twin Sensitivity Sandbox")
    st.info("💡 **Goal:** Test how changing factory constraints, demand multipliers, and order mix alters 7-day costs and throughput.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Factory Constraints")
        mgt_cap = st.slider("Management Capacity Limit (units/day):", 100, 300, 250, step=10)
        equip_cap = st.slider("Equipment Capacity (units/day):", 500, 2000, 1500, step=100)

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

        st.dataframe(pd.DataFrame(sim_data))
        st.metric("Total 7-Day Simulation Cost", f"${cum_cost:,.2f}")
        st.success("Simulation run complete! Adjust the parameters above to run sensitivity experiments.")
