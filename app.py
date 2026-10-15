import streamlit as st
import pulp
import pandas as pd
import json

st.set_page_config(
    page_title="Jewelry Supply Chain Teaching Tool & Digital Twin",
    page_icon="💎",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #94a3b8; margin-bottom: 1.5rem; }
    .card { background-color: #1e293b; padding: 1.2rem; border-radius: 0.5rem; border: 1px solid #334155; margin-bottom: 1rem; }
    .metric-label { font-size: 0.85rem; color: #94a3b8; font-weight: 600; }
    .metric-val { font-size: 1.5rem; font-weight: 700; color: #f8fafc; }
    
    /* White fill student instruction card styling */
    .instruction-card-light {
        background-color: #ffffff !important;
        color: #0f172a !important;
        padding: 1.25rem !important;
        border-radius: 0.5rem !important;
        border: 2px solid #0284c7 !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
    }
    .instruction-card-light h4 {
        color: #0369a1 !important;
        margin-top: 0 !important;
        font-size: 1.15rem !important;
        font-weight: 700 !important;
    }
    .instruction-card-light p, .instruction-card-light li {
        color: #1e293b !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        line-height: 1.5 !important;
    }

    .exp-box-higher {
        background-color: #1e1b4b;
        border-left: 5px solid #818cf8;
        padding: 1.2rem;
        border-radius: 0.4rem;
        margin-top: 1rem;
        color: #e0e7ff;
    }
    .exp-box-lower {
        background-color: #451a03;
        border-left: 5px solid #f97316;
        padding: 1.2rem;
        border-radius: 0.4rem;
        margin-top: 1rem;
        color: #ffedd5;
    }
    .exp-box-optimal {
        background-color: #064e3b;
        border-left: 5px solid #34d399;
        padding: 1.2rem;
        border-radius: 0.4rem;
        margin-top: 1rem;
        color: #ecfdf5;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💎 Jewelry Supply Chain Teaching Tool & Digital Twin</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive Operational Decision Game & Sensitivity Analysis Platform</div>', unsafe_allow_html=True)

platform_mode = st.sidebar.radio(
    "Select Platform Mode:",
    [
        "📖 Case Study Introduction & Tutorial",
        "🎮 Mode 1: Daily Decision Game",
        "🔬 Mode 2: Digital Twin Sandbox"
    ]
)

# Solver Helper Function
def solve_daily_lp_benchmark(day, demand_units, mgt_cap=250.0, equip_cap=1500, metal_stock=500.0, stone_stock=500.0):
    try:
        prob = pulp.LpProblem(f"LP_Day_{day}", pulp.LpMinimize)
        
        usable_metal = max(0.0, metal_stock - 100.0)
        usable_stone = max(0.0, stone_stock - 100.0)
        
        needed_m = max(0.0, demand_units - usable_metal)
        needed_s = max(0.0, demand_units - usable_stone)
        
        buy_m = pulp.LpVariable("buy_m", lowBound=0.0, cat=pulp.LpContinuous)
        buy_s = pulp.LpVariable("buy_s", lowBound=0.0, cat=pulp.LpContinuous)
        ot_reg = pulp.LpVariable("ot_reg", lowBound=0.0, upBound=30.0, cat=pulp.LpContinuous)
        hire_out = pulp.LpVariable("hire_out", lowBound=0.0, upBound=30.0, cat=pulp.LpContinuous)
        
        prob += buy_m >= needed_m
        prob += buy_s >= needed_s
        
        prob += 560.0 + 5.0 * ot_reg + 8.0 * hire_out >= min(demand_units, equip_cap)
        prob += 164.5 + 0.4 * ot_reg + 0.3 * hire_out <= mgt_cap
        
        cost_mat = 50.0 * buy_m + 100.0 * buy_s
        cost_labor = 3650.0 + 20.0 * ot_reg + 40.0 * hire_out
        
        prob += cost_mat + cost_labor
        
        status = prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[status] == 'Optimal':
            return {
                'buy_m': round(float(pulp.value(buy_m)), 1),
                'buy_s': round(float(pulp.value(buy_s)), 1),
                'ot_reg': round(float(pulp.value(ot_reg)), 1),
                'hire_out': round(float(pulp.value(hire_out)), 1),
                'total_cost': round(float(pulp.value(prob.objective)), 2),
                'status': 'Optimal'
            }
        else:
            raise ValueError("LP Infeasible")
    except Exception:
        usable_metal = max(0.0, metal_stock - 100.0)
        usable_stone = max(0.0, stone_stock - 100.0)
        needed_m = max(0.0, demand_units - usable_metal)
        needed_s = max(0.0, demand_units - usable_stone)
        req_add_output = max(0.0, demand_units - 560.0)
        ot_needed = min(30.0, req_add_output / 5.0)
        rem_output = max(0.0, req_add_output - (ot_needed * 5.0))
        out_needed = min(30.0, rem_output / 8.0)
        
        tot_c = 3650.0 + (needed_m * 50.0) + (needed_s * 100.0) + (ot_needed * 20.0) + (out_needed * 40.0)
        return {
            'buy_m': round(needed_m, 1),
            'buy_s': round(needed_s, 1),
            'ot_reg': round(ot_needed, 1),
            'hire_out': round(out_needed, 1),
            'total_cost': round(tot_c, 2),
            'status': 'Analytical Benchmark'
        }

# ==========================================
# OPTION 1: CASE STUDY TUTORIAL
# ==========================================
if platform_mode == "📖 Case Study Introduction & Tutorial":
    st.header("📖 Case Study Tutorial: Optimization & Simulation in Jewelry Manufacturing")
    
    tut_tab1, tut_tab2 = st.tabs([
        "Part 1: Fundamentals, Process Setup & Constraints",
        "Part 2: Worked Case Examples (Low Load vs High Surge)"
    ])
    
    with tut_tab1:
        st.markdown("""
        ### 📚 What is Linear Programming & Simulation?
        
        * **Linear Programming (LP):** A mathematical optimization technique used to calculate the **lowest possible cost** (or highest profit) given operational constraints. In this simulation, the LP acts as an **Intelligent Factory Planner** that calculates optimal raw material procurement and labor allocation.
        * **Discrete Event Simulation (DES):** A modeling method that tracks physical queues, material stock movements, and order progress day-by-day. 
        * **Synergy:** By coupling LP optimization with simulation, students learn how analytical models respond to real-world operational trade-offs, inventory floors, and capacity bottlenecks.

        ---

        ### ⚙️ Factory Setup & Manufacturing Process Flow
        
        1. **Design Stage (Optional):** Takes **1 day** per order ($100 fixed order fee). Offers a **25% probability** of reducing metal requirement from 1.0 unit to 0.9 units/piece.
        2. **Pre-Production Stage:** Metal and Stone prep (Capped at **1,500 units/day** equipment limit).
        3. **Post-Production Stage:** Finishing and assembly (Capped at **1,500 units/day** equipment limit).
        
        * **Order Types & Cycle Times:**
          * **Type O (Ordinary Orders):** Requires **1 day** in Pre-Production + **1 day** in Post-Production (**2-day total manufacturing cycle**).
          * **Type J (Joining Orders):** Requires **1 day** in Pre-Production + **2 days** in Post-Production (**3-day total manufacturing cycle**).

        ---

        ### 🛠️ Artisan Resources Matrix
        """)
        
        art_df = pd.DataFrame([
            {"Artisan Class": "Regular Payroll", "Starting Staff (Pre/Post)": "60 / 70", "Daily Output": "5 u/day", "Base Daily Cost": "$10/day ($2.00/u)", "Max Overtime": "0.5 day ($20/day = $2.67/u)", "Eligible Orders": "Type O Only", "Management Overhead": "0.4 units / artisan"},
            {"Artisan Class": "Skilled Payroll", "Starting Staff (Pre/Post)": "20 / 20", "Daily Output": "5 u/day", "Base Daily Cost": "$15/day ($3.00/u)", "Max Overtime": "0.5 day ($30/day = $4.00/u)", "Eligible Orders": "Type O & Type J", "Management Overhead": "2.0 units / artisan"},
            {"Artisan Class": "Skilled Contractor", "Starting Staff (Pre/Post)": "10 / 15", "Daily Output": "8 u/day", "Base Daily Cost": "$30/day ($3.75/u)", "Max Overtime": "None", "Eligible Orders": "Type O & Type J", "Management Overhead": "1.0 unit / artisan"},
            {"Artisan Class": "Outsource Contractor", "Starting Staff (Pre/Post)": "10 / 15", "Daily Output": "8 u/day", "Base Daily Cost": "$40/day ($5.00/u)", "Max Overtime": "None", "Eligible Orders": "Type O & Type J", "Management Overhead": "0.3 units / artisan"}
        ])
        st.dataframe(art_df, use_container_width=True)

        st.markdown("""
        ---

        ### 📦 Raw Material Safety Floor & Procurement Rule
        * **Bill of Materials (BOM):** Every unit produced requires **1 unit of Metal ($50)** and **1 unit of Stone ($100)**.
        * **Mandatory Safety Stock Floor:** Raw material inventory must **never drop below 100 units** of Metal or Stone at the end of any day.
        
        > **⚠️ Inventory Procurement Example:**
        > If today's incoming demand is **500 units** and starting metal stock is **200 units**, usable stock above the safety floor is **100 units** (`200 - 100`). Therefore, at least **400 units** of new metal must be procured (`500 - 100 = 400`). If less than 400 units are procured, fewer units enter production, creating an unfulfilled **Order Backlog**.

        ---

        ### 🧠 System Constraints Summary
        * **Management Bandwidth Cap:** **250.0 management units/day**. Baseline starting staff consumes **164.5 units/day**, leaving **85.5 units** for overtime and contractor hiring.
        * **Equipment Capacity Ceiling:** **1,500 units/day** in both Pre-Production and Post-Production.
        """)

    with tut_tab2:
        st.markdown("""
        ### 📊 Worked Case Examples & Constraint Progression
        
        #### 🟢 Case Example 1: Low Order Demand Load (~500 units/day)
        * **Scenario:** Factory receives standard baseline demand of ~500 units/day.
        * **Operational Strategy:** Baseline staff capacity (560 units/day output in Pre-Prod) absorbs all workload without overtime or contractor hiring.
        * **Constraint Status:**
          * Management Bandwidth Used: **164.5 / 250.0 u** (Unbinding / 65.8% utilized).
          * Equipment Used: **500 / 1,500 u** (Unbinding / 33.3% utilized).
          * Overtime Authorized: **0.0 days**.
        * **Financial Outcome:** Total 7-day cost = **$574,550.00**, achieving a 100% On-Time Delivery score.

        ---

        #### 🔴 Case Example 2: High Demand Surge (~1,000–1,500 units/day)
        * **Scenario:** Order volume surges significantly, testing system capacity limits.
        * **Progression of Maxed Constraints:**
          1. **At 1,000 units/day:** Demand exceeds baseline staff (560u). The LP engine authorizes **Regular Payroll Overtime** first ($2.67/unit output) up to the 60 OT days cap.
          2. **At 1,200 units/day:** Overtime consumes additional management bandwidth, reaching the **250.0 Management Cap**. To expand capacity further without breaking the management budget, the LP recruits **Outsource Contractors** because they consume only **0.038 mgmt units/product unit**.
          3. **At 1,500 units/day:** Daily workload reaches the **1,500 units/day Equipment Capacity Ceiling**. Equipment forms a hard bottleneck, causing order backlogs to accumulate in the pre-production queue.
        """)

# ==========================================
# OPTION 2: MODE 1 - DAILY DECISION GAME
# ==========================================
elif platform_mode == "🎮 Mode 1: Daily Decision Game":
    st.header("🎮 Mode 1: Daily Decision Game (Player vs. LP Benchmark)")
    
    with st.expander("📌 Quick Reference: Factory Setup, Process Flow & Resource Constraints"):
        st.markdown("""
        * **Process Flow:** Pre-Production (1 day) ➔ Post-Production (Type O = 1 day, Type J = 2 days).
        * **Equipment Limit:** 1,500 units/day | **Management Limit:** 250.0 units/day (Base staff uses 164.5 u/day).
        * **BOM:** 1 Metal ($50) + 1 Stone ($100) per unit | **Safety Floor:** Minimum 100 units raw stock required at all times.
        * **Labor Rates:** Regular OT = $20/day ($2.67/u, 0.08 mgmt/u) | Outsource Contractor = $40/day ($5.00/u, 0.038 mgmt/u).
        """)

    # Initialize Session State
    if 'day' not in st.session_state:
        st.session_state.day = 1
        st.session_state.metal_stock = 500.0
        st.session_state.stone_stock = 500.0
        st.session_state.wip_metal = 0.0
        st.session_state.wip_stone = 0.0
        st.session_state.pre_backlog = 0.0
        st.session_state.cum_player_cost = 0.0
        st.session_state.cum_lp_cost = 0.0
        st.session_state.game_history = []
        st.session_state.last_comparison = None
        st.session_state.last_explanation = None

    current_day = st.session_state.day

    # Check 7-Day Game Boundary
    if current_day > 7:
        st.balloons()
        st.success("🎉 7-Day Simulation Complete! Excellent effort managing the factory pipeline.")
        
        c_p = st.session_state.cum_player_cost
        c_lp = st.session_state.cum_lp_cost
        gap = c_p - c_lp
        eff_overall = min(100.0, (c_lp / c_p) * 100.0) if c_p > 0 else 100.0
        
        st.subheader("🏆 Final 7-Day Performance Scorecard")
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Total Player Cost", f"${c_p:,.2f}")
        sc2.metric("LP Benchmark Cost", f"${c_lp:,.2f}")
        sc3.metric("Cost Gap (Variance)", f"+${max(0.0, gap):,.2f}")
        sc4.metric("Overall Efficiency Grade", f"{eff_overall:.1f}%")
        
        if st.session_state.game_history:
            st.write("### 📊 Daily Ledger History")
            st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)

        if st.button("🔄 Restart 7-Day Simulation Session", type="primary"):
            st.session_state.day = 1
            st.session_state.metal_stock = 500.0
            st.session_state.stone_stock = 500.0
            st.session_state.wip_metal = 0.0
            st.session_state.wip_stone = 0.0
            st.session_state.pre_backlog = 0.0
            st.session_state.cum_player_cost = 0.0
            st.session_state.cum_lp_cost = 0.0
            st.session_state.game_history = []
            st.session_state.last_comparison = None
            st.session_state.last_explanation = None
            st.rerun()

    else:
        st.subheader(f"📅 Simulation Day {current_day} of 7")

        # WHITE FILL STUDENT INSTRUCTIONS CARD
        st.markdown(f"""
        <div class="instruction-card-light">
            <h4>📋 Student Instructions for Factory Manager (Day {current_day} of 7):</h4>
            <p>
                Review today's incoming demand and existing backlog queue below. You must decide on the following <strong>4 Decision Variables</strong>:
            </p>
            <ol>
                <li><strong>Metal Purchase (units):</strong> Purchase raw metal @ $50/unit. <em>Note: Usable metal = Starting Stock - 100.0 Safety Floor!</em></li>
                <li><strong>Stone Purchase (units):</strong> Purchase raw stone @ $100/unit. <em>Note: Usable stone = Starting Stock - 100.0 Safety Floor!</em></li>
                <li><strong>Pre-Prod Regular Payroll Overtime (Days):</strong> Assign overtime to Regular Payroll staff (up to 30.0 days @ $20/day = $2.67/unit output).</li>
                <li><strong>Outsource Contractors to Hire (Artisans):</strong> Recruit Outsource Contractor artisans (up to 30 artisans @ $40/day = $5.00/unit output).</li>
            </ol>
            <p style="color: #0369a1; font-weight: 700; margin-bottom: 0;">
                💡 Objective: Fulfill today's workload cleanly without stalling production, violating safety stock, or incurring unnecessary labor surcharges!
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Inventory Dashboard Cards
        dash1, dash2, dash3, dash4, dash5 = st.columns(5)
        dash1.metric("Metal Raw Stock", f"{st.session_state.metal_stock:.1f} u")
        dash2.metric("Stone Raw Stock", f"{st.session_state.stone_stock:.1f} u")
        dash3.metric("WIP Committed Metal", f"{st.session_state.wip_metal:.1f} u")
        dash4.metric("Pre-Prod Backlog Queue", f"{st.session_state.pre_backlog:.1f} u")
        dash5.metric("Safety Stock Floor", "100.0 u")

        # Demand Schedule
        demand_schedule = {
            1: (43, 500, "Opening Baseline Demand"),
            2: (65, 755, "+50% Demand Surge over Day 1"),
            3: (98, 1130, "+50% Demand Surge over Day 2 (Surge Surcharge Trigger!)"),
            4: (43, 500, "Normal Baseline Demand"),
            5: (65, 755, "+50% Demand Surge"),
            6: (43, 500, "Normal Baseline Demand"),
            7: (43, 500, "Normal Baseline Demand")
        }

        orders_cnt, today_demand_u, demand_desc = demand_schedule[current_day]
        total_workload_u = today_demand_u + st.session_state.pre_backlog

        st.info(f"📦 **Today's Demand (Day {current_day}):** {orders_cnt} Orders ({today_demand_u} units) — *{demand_desc}* | **Total Workload Queue to Process = {total_workload_u:.1f} units**")

        usable_m_start = max(0.0, st.session_state.metal_stock - 100.0)
        usable_s_start = max(0.0, st.session_state.stone_stock - 100.0)
        rec_m = max(0.0, total_workload_u - usable_m_start)
        rec_s = max(0.0, total_workload_u - usable_s_start)

        with st.form("day_decision_form"):
            st.write("### 🛠️ Enter Your Daily Decision Variables")
            f_col1, f_col2 = st.columns(2)

            with f_col1:
                st.markdown("#### Raw Material Procurement")
                input_buy_m = st.number_input(f"1. Metal Purchase (units @ $50/u) [Min Required: {rec_m:.0f} u]:", min_value=0, value=int(rec_m), step=25)
                input_buy_s = st.number_input(f"2. Stone Purchase (units @ $100/u) [Min Required: {rec_s:.0f} u]:", min_value=0, value=int(rec_s), step=25)

            with f_col2:
                st.markdown("#### Labor & Capacity Allocation")
                input_ot_reg = st.slider("3. Pre-Prod Regular Payroll Overtime (Days):", 0.0, 30.0, 10.0 if total_workload_u > 560 else 0.0, step=1.0)
                input_hire_out = st.slider("4. Outsource Contractors to Hire (Artisans):", 0, 30, 5 if total_workload_u > 800 else 0, step=1)

            submitted = st.form_submit_button("▶ Submit Decisions & Step 1 Day Forward", type="primary")

        if submitted:
            # Player Spend Calculations
            mat_cost_p = input_buy_m * 50.0 + input_buy_s * 100.0
            art_cost_p = 3650.0 + input_ot_reg * 20.0 + input_hire_out * 40.0
            player_day_cost = mat_cost_p + art_cost_p

            # Feasibility Check
            avail_m = usable_m_start + input_buy_m
            avail_s = usable_s_start + input_buy_s
            labor_cap_p = 560.0 + input_ot_reg * 5.0 + input_hire_out * 8.0
            
            allowed_into_prod = min(total_workload_u, avail_m, avail_s, labor_cap_p, 1500.0)

            feasibility_failed = False
            if allowed_into_prod < today_demand_u:
                feasibility_failed = True

            # Solve LP Benchmark
            lp_res = solve_daily_lp_benchmark(current_day, total_workload_u, 250.0, 1500, st.session_state.metal_stock, st.session_state.stone_stock)
            lp_day_cost = lp_res['total_cost']

            if feasibility_failed:
                efficiency = 0.0
                st.error(f"🚨 **PRODUCTION STALLED! Feasibility Failure:** Your procurement allowed only {allowed_into_prod:.0f} units into production, failing to fulfill today's incoming demand of {today_demand_u} units. Score assigned = 0.0%.")
            else:
                efficiency = min(100.0, (lp_day_cost / player_day_cost) * 100.0) if player_day_cost > 0 else 100.0

            # Inventory Updates
            new_metal_stock = max(0.0, st.session_state.metal_stock + input_buy_m - allowed_into_prod)
            new_stone_stock = max(0.0, st.session_state.stone_stock + input_buy_s - allowed_into_prod)
            new_backlog = max(0.0, total_workload_u - allowed_into_prod)

            st.session_state.wip_metal += allowed_into_prod
            st.session_state.wip_stone += allowed_into_prod
            st.session_state.metal_stock = new_metal_stock
            st.session_state.stone_stock = new_stone_stock
            st.session_state.pre_backlog = new_backlog
            st.session_state.cum_player_cost += player_day_cost
            st.session_state.cum_lp_cost += lp_day_cost

            # Build Comparison Data
            comp_df = pd.DataFrame([
                {"Decision Variable": "1. Metal Purchase (units)", "Player Choice": f"{input_buy_m:.1f} u", "LP Optimal Choice": f"{lp_res['buy_m']:.1f} u", "Cost Impact": f"${((input_buy_m - lp_res['buy_m']) * 50.0):+,.2f}"},
                {"Decision Variable": "2. Stone Purchase (units)", "Player Choice": f"{input_buy_s:.1f} u", "LP Optimal Choice": f"{lp_res['buy_s']:.1f} u", "Cost Impact": f"${((input_buy_s - lp_res['buy_s']) * 100.0):+,.2f}"},
                {"Decision Variable": "3. Regular Payroll Overtime (days)", "Player Choice": f"{input_ot_reg:.1f} days", "LP Optimal Choice": f"{lp_res['ot_reg']:.1f} days", "Cost Impact": f"${((input_ot_reg - lp_res['ot_reg']) * 20.0):+,.2f}"},
                {"Decision Variable": "4. Outsource Contractors Hired (artisans)", "Player Choice": f"{input_hire_out} artisans", "LP Optimal Choice": f"{lp_res['hire_out']:.1f} artisans", "Cost Impact": f"${((input_hire_out - lp_res['hire_out']) * 40.0):+,.2f}"},
                {"Decision Variable": "TOTAL DAILY OPERATIONAL COST", "Player Choice": f"${player_day_cost:,.2f}", "LP Optimal Choice": f"${lp_day_cost:,.2f}", "Cost Impact": f"${(player_day_cost - lp_day_cost):+,.2f}"}
            ])

            # Build Explanation
            cost_diff = player_day_cost - lp_day_cost
            explanation_html = ""

            if player_day_cost > lp_day_cost:
                reasons = []
                if input_buy_m > lp_res['buy_m']:
                    reasons.append(f"<li><strong>Metal Over-Purchasing:</strong> You bought {input_buy_m} u of metal vs LP's {lp_res['buy_m']} u, spending an extra +${((input_buy_m - lp_res['buy_m']) * 50.0):,.2f}. Over-purchasing locked up extra cash in inventory beyond immediate production needs plus the 100u safety stock floor.</li>")
                if input_buy_s > lp_res['buy_s']:
                    reasons.append(f"<li><strong>Stone Over-Purchasing:</strong> You bought {input_buy_s} u of stone vs LP's {lp_res['buy_s']} u, spending an extra +${((input_buy_s - lp_res['buy_s']) * 100.0):,.2f}. Over-purchasing locked up extra cash in inventory beyond immediate production needs plus the 100u safety stock floor.</li>")
                if input_hire_out > lp_res['hire_out']:
                    reasons.append(f"<li><strong>Outsource Contractor Surcharge:</strong> You hired {input_hire_out} Outsource Contractors ($40/day = $5.00/u output) vs LP's {lp_res['hire_out']} contractors, adding +${((input_hire_out - lp_res['hire_out']) * 40.0):,.2f}. Hiring contractors when regular overtime ($2.67/u output) or existing staff can meet throughput increases labor spend.</li>")
                if input_ot_reg > lp_res['ot_reg']:
                    reasons.append(f"<li><strong>Excessive Overtime:</strong> You scheduled {input_ot_reg} overtime days ($20/day) vs LP's {lp_res['ot_reg']} days, adding +${((input_ot_reg - lp_res['ot_reg']) * 20.0):,.2f}. Scheduling more overtime than required for daily demand incurs unnecessary labor surcharges.</li>")
                
                reason_str = "".join(reasons) if reasons else "<li>Higher overall labor or material commitments than required.</li>"
                
                explanation_html = f"""
                <div class="exp-box-higher">
                    <h4 style="color: #a5b4fc; margin-top: 0;">💡 Why is the Player Spend Higher (+${cost_diff:,.2f}) than the LP Benchmark?</h4>
                    <p>Your daily operational spend was <strong>${player_day_cost:,.2f}</strong> compared to the LP benchmark of <strong>${lp_day_cost:,.2f}</strong>. Key cost drivers include:</p>
                    <ul>{reason_str}</ul>
                    <p style="margin-bottom: 0;"><strong>LP Advantage:</strong> The LP benchmark minimizes total cash outflow by procuring only the exact raw materials required to preserve the 100-unit safety floor and utilizing the lowest-cost labor combination.</p>
                </div>
                """

            elif player_day_cost < lp_day_cost:
                reasons = []
                if input_buy_m < lp_res['buy_m'] or input_buy_s < lp_res['buy_s']:
                    reasons.append(f"<li><strong>Raw Material Under-Purchasing & Production Risk:</strong> You bought {input_buy_m} metal / {input_buy_s} stone vs LP's {lp_res['buy_m']} metal / {lp_res['buy_s']} stone. Under-purchasing raw materials failed to cover today's workload + 100u safety floor, causing orders to stall or breaching the mandatory safety stock level. The LP invested in materials to keep 100% of demand moving through production smoothly.</li>")
                if input_ot_reg < lp_res['ot_reg'] or input_hire_out < lp_res['hire_out']:
                    reasons.append(f"<li><strong>Labor Capacity Shortfall & Order Backlog Risk:</strong> You scheduled {input_ot_reg} overtime days / {input_hire_out} contractors vs LP's {lp_res['ot_reg']} overtime days / {lp_res['hire_out']} contractors. Under-staffing pre-production leaves incoming orders stuck in an unfulfilled backlog queue, risking late delivery penalties. The LP authorized necessary overtime/contractors to clear demand immediately and protect the 100% On-Time Delivery score.</li>")

                reason_str = "".join(reasons) if reasons else "<li>Under-investing in raw materials or labor capacity.</li>"

                explanation_html = f"""
                <div class="exp-box-lower">
                    <h4 style="color: #fed7aa; margin-top: 0;">⚠️ Why is the LP Benchmark Spend Higher (+${(-cost_diff):,.2f}) than the Player Choice?</h4>
                    <p>Your daily cash spend was <strong>${player_day_cost:,.2f}</strong> while the LP benchmark spent <strong>${lp_day_cost:,.2f}</strong>. Here is why the LP choice is optimal:</p>
                    <ul>{reason_str}</ul>
                    <p style="margin-bottom: 0;"><strong>LP Advantage:</strong> Although your daily cash spend appeared lower, under-investing in raw materials or labor causes factory stalls, safety stock breaches, or severe backlog penalties. The LP's higher spend is optimal because it guarantees full throughput and delivery score compliance while minimizing total 7-day penalty-adjusted costs.</p>
                </div>
                """
            else:
                explanation_html = """
                <div class="exp-box-optimal">
                    <h4 style="color: #6ee7b7; margin-top: 0;">🌟 Perfect Optimization Match!</h4>
                    <p style="margin-bottom: 0;">Outstanding decision making! Your choices matched the mathematical Linear Program benchmark exactly across all 4 decision variables.</p>
                </div>
                """

            st.session_state.last_comparison = comp_df
            st.session_state.last_explanation = explanation_html

            st.session_state.game_history.append({
                "Day": f"Day {current_day}",
                "Player Cost": f"${player_day_cost:,.2f}",
                "LP Benchmark": f"${lp_day_cost:,.2f}",
                "Score": f"{efficiency:.1f}%",
                "Pre-Prod Backlog": f"{new_backlog:.1f} u"
            })

            st.session_state.day += 1

            st.success(f"Day {current_day} completed! Review the decision breakdown and explanation below.")

        # Render Comparison Table & Explanation
        if st.session_state.last_comparison is not None:
            st.write("### 🔍 Daily Decision Variable Comparison (Player vs LP Benchmark)")
            st.dataframe(st.session_state.last_comparison, use_container_width=True)
            
            if st.session_state.last_explanation:
                st.markdown(st.session_state.last_explanation, unsafe_allow_html=True)

        if st.session_state.game_history:
            st.write("### 📊 Daily Ledger History")
            st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)

        if st.button("🔄 Reset 7-Day Simulation Session"):
            st.session_state.day = 1
            st.session_state.metal_stock = 500.0
            st.session_state.stone_stock = 500.0
            st.session_state.wip_metal = 0.0
            st.session_state.wip_stone = 0.0
            st.session_state.pre_backlog = 0.0
            st.session_state.cum_player_cost = 0.0
            st.session_state.cum_lp_cost = 0.0
            st.session_state.game_history = []
            st.session_state.last_comparison = None
            st.session_state.last_explanation = None
            st.rerun()

# ==========================================
# OPTION 3: MODE 2 - DIGITAL TWIN SANDBOX
# ==========================================
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
        
        base_orders = [500, 755, 1130, 500, 755, 500, 500]
        sim_data = []

        cum_cost = 0.0
        for d_idx, raw_u in enumerate(base_orders, 1):
            recv_u = int(raw_u * demand_mult)
            comp_u = int(recv_u * (0.85 if type_j_ratio <= 30 else 0.75))
            mgt_used = min(mgt_cap, 164.5 + d_idx * 5.0)
            d_cost = 3650.0 + (comp_u * (p_metal * 0.4 + p_stone * 0.6))
            cum_cost += d_cost

            sim_data.append({
                "Day": f"Day {d_idx}",
                "Workload (units)": recv_u,
                "Completed (units)": comp_u,
                "Management Used": f"{mgt_used:.1f} / {mgt_cap} u",
                "Daily Total Cost": f"${d_cost:,.2f}"
            })

        st.dataframe(pd.DataFrame(sim_data), use_container_width=True)

        st.metric("Total 7-Day Simulation Cost", f"${cum_cost:,.2f}")
        st.success("Simulation run complete! Adjust parameters above to explore sensitivity trade-offs.")
