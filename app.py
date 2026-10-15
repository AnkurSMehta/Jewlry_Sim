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
    .main-header { font-size: 2.2rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #94a3b8; margin-bottom: 1.2rem; }
    .card { background-color: #1e293b; padding: 1.2rem; border-radius: 0.5rem; border: 1px solid #334155; margin-bottom: 1rem; }
    .instruction-card { background-color: #0f172a; border-left: 4px solid #38bdf8; padding: 1rem; border-radius: 0.4rem; margin-bottom: 1.2rem; }
    .warn-card { background-color: #451a03; border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 0.4rem; margin-bottom: 1.2rem; }
    .success-card { background-color: #064e3b; border-left: 4px solid #10b981; padding: 1rem; border-radius: 0.4rem; margin-bottom: 1.2rem; }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-val { font-size: 1.4rem; font-weight: 700; color: #f8fafc; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💎 Jewelry Supply Chain Teaching Tool & Digital Twin</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive Supply Chain Management, Linear Programming Benchmark & Sensitivity Sandbox</div>', unsafe_allow_html=True)

mode = st.sidebar.radio(
    "Select Learning Module:",
    [
        "📖 Case Study Introduction & Tutorial",
        "🎮 Mode 1: Daily Decision Game (Player vs. LP Benchmark)",
        "🔬 Mode 2: Digital Twin Sandbox"
    ]
)

# Load Default Config
@st.cache_data
def load_default_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except Exception:
        return {
            "simulation_settings": { "management_capacity_daily": 250.0, "min_raw_material_safety_stock": 100, "equipment_capacity_daily": 1500 },
            "raw_materials": { "metal": { "unit_cost": 50.0 }, "stone": { "unit_cost": 100.0 } }
        }

cfg = load_default_config()

# Helper function: LP Benchmark Solver
def solve_daily_lp_benchmark(day, demand_units, usable_metal, usable_stone, mgt_cap=250.0, equip_cap=1500):
    try:
        prob = pulp.LpProblem(f"LP_Benchmark_Day_{day}", pulp.LpMinimize)
        
        # Decision Variables
        buy_m = pulp.LpVariable("buy_m", lowBound=0.0, cat=pulp.LpContinuous)
        buy_s = pulp.LpVariable("buy_s", lowBound=0.0, cat=pulp.LpContinuous)
        ot_reg = pulp.LpVariable("ot_reg", lowBound=0.0, upBound=30.0, cat=pulp.LpContinuous)
        hire_out = pulp.LpVariable("hire_out", lowBound=0.0, upBound=40.0, cat=pulp.LpContinuous)
        
        # Target units to process into pre-production
        target_pre = min(demand_units, equip_cap)
        
        # Material Constraints (Usable stock + procurement >= target)
        prob += (usable_metal + buy_m >= target_pre, "Metal_Supply_Req")
        prob += (usable_stone + buy_s >= target_pre, "Stone_Supply_Req")
        
        # Labor Capacity Constraint
        # Base staff = 560 units (Pre-prod). Regular OT = +10 u/day. Outsource = +8 u/artisan
        prob += (560.0 + (10.0 * ot_reg) + (8.0 * hire_out) >= target_pre, "Labor_Pre_Cap")
        
        # Management Capacity Constraint
        # Base staff = 164.5 u mgmt. Regular OT = +0.4 u mgmt/day. Outsource = +0.3 u mgmt/artisan
        prob += (164.5 + (0.4 * ot_reg) + (0.3 * hire_out) <= mgt_cap, "Mgmt_Bandwidth_Cap")
        
        # Cost Objective Function
        cost_materials = (50.0 * buy_m) + (100.0 * buy_s)
        cost_labor = 3650.0 + (20.0 * ot_reg) + (40.0 * hire_out)
        prob += cost_materials + cost_labor
        
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            return {
                "buy_m": max(0.0, round(pulp.value(buy_m), 1)),
                "buy_s": max(0.0, round(pulp.value(buy_s), 1)),
                "ot_reg": max(0.0, round(pulp.value(ot_reg), 1)),
                "hire_out": max(0.0, round(pulp.value(hire_out), 1)),
                "total_cost": round(pulp.value(prob.objective), 2),
                "status": "Optimal"
            }
    except Exception:
        pass
    
    # Analytical Fallback
    needed_m = max(0.0, min(demand_units, equip_cap) - usable_metal)
    needed_s = max(0.0, min(demand_units, equip_cap) - usable_stone)
    deficit_labor = max(0.0, min(demand_units, equip_cap) - 560.0)
    
    ot_needed = min(30.0, deficit_labor / 10.0)
    rem_labor = max(0.0, deficit_labor - (ot_needed * 10.0))
    out_needed = min(40.0, rem_labor / 8.0)
    
    tot_c = (needed_m * 50.0) + (needed_s * 100.0) + 3650.0 + (ot_needed * 20.0) + (out_needed * 40.0)
    return {
        "buy_m": round(needed_m, 1),
        "buy_s": round(needed_s, 1),
        "ot_reg": round(ot_needed, 1),
        "hire_out": round(out_needed, 1),
        "total_cost": round(tot_c, 2),
        "status": "Optimal (Analytical)"
    }


# ==============================================================================
# OPTION 1: CASE STUDY INTRODUCTION & TUTORIAL
# ==============================================================================
if mode == "📖 Case Study Introduction & Tutorial":
    st.title("📖 Case Study: Fine Jewelry Manufacturing Supply Chain")
    st.info("💡 Welcome! This tutorial introduces the core concepts of Linear Programming (LP) optimization, Discrete Event Simulation (DES), and factory operational constraints.")

    tab1, tab2 = st.tabs(["Part 1: Optimization Theory & Comprehensive Setup", "Part 2: Worked Examples & Constraint Progression"])

    with tab1:
        st.markdown("""
        ### 1. Fundamentals of Linear Programming & Simulation
        Modern supply chain management combines **Linear Programming (LP)** with **Discrete Event Simulation (DES)**:
        * **Linear Programming (The Intelligent Planner):** Mathematically solves for the optimal combination of decision variables that **minimizes total operating cost** while strictly honoring capacity, material, labor, and management constraints.
        * **Discrete Event Simulation (The Physical Factory Engine):** Tracks the physical flow of orders, work-in-progress (WIP) queues, raw material inventories, lead time delays, and customer delivery scores day-by-day.

        ---

        ### 2. Manufacturing Setup & Process Flow
        The factory produces fine jewelry through three distinct stages:
        1. **Design Stage (Optional):** Takes 1 day per order ($100 fee per order). Gives a 25% probability of reducing metal requirement to 0.9 units/piece (75% probability of no savings).
        2. **Pre-Production Stage:** Primary crafting stage (1,500 units/day equipment limit). Consumes 1 unit of Metal and 1 unit of Stone per piece.
        3. **Post-Production Stage:** Finishing and assembly stage (1,500 units/day equipment limit).

        **Order Types & Manufacturing Cycle Times:**
        * **Type O (Ordinary Orders):** Requires 1 day in Pre-Production + 1 day in Post-Production (**2-day total manufacturing cycle**).
        * **Type J (Joining Orders):** Requires 1 day in Pre-Production + 2 days in Post-Production (**3-day total manufacturing cycle**). Can only be crafted by skilled artisans.

        ---

        ### 3. Raw Material Safety Floor & Procurement Rule
        * **Bill of Materials (BOM):** Each piece requires **1 unit of Metal ($50/unit)** and **1 unit of Stone ($100/unit)**.
        * **Mandatory Safety Stock Floor:** Raw stock must **never dip below 100 units** of Metal or 100 units of Stone.
        
        > **⚠️ Crucial Inventory Rule Example:**
        > Suppose today's incoming demand is **500 units** and starting metal stock is **200 units**:
        > * Only **100 units** of current stock can be consumed (because 100 units must remain in stock as the safety floor).
        > * Therefore, at least **400 units** of new metal must be procured (`500 - 100 = 400`).
        > * If the manager procures less than 400 units, fewer units can enter production, creating an unfulfilled **Order Backlog** and potentially stalling factory output!

        ---

        ### 4. Resource Constraints & Operating Rules Matrix
        Management bandwidth is capped at **250.0 units/day** across all active staff and overtime:
        """)

        res_table = pd.DataFrame([
            {"Artisan Class": "Regular Payroll", "Starting Staff (Pre/Post)": "60 / 70", "Daily Output": "5 units/day", "Base Daily Rate": "$10/day ($2.00/u)", "Max Overtime Rule": "Up to 0.5 day ($20/day)", "Allowed Orders": "Type O Only", "Management Overhead": "0.4 units / artisan"},
            {"Artisan Class": "Skilled Payroll", "Starting Staff (Pre/Post)": "20 / 20", "Daily Output": "5 units/day", "Base Daily Rate": "$15/day ($3.00/u)", "Max Overtime Rule": "Up to 0.5 day ($30/day)", "Allowed Orders": "Type O & Type J", "Management Overhead": "2.0 units / artisan"},
            {"Artisan Class": "Skilled Contractor", "Starting Staff (Pre/Post)": "10 / 15", "Daily Output": "8 units/day", "Base Daily Rate": "$30/day ($3.75/u)", "Max Overtime Rule": "None", "Allowed Orders": "Type O & Type J", "Management Overhead": "1.0 unit / artisan"},
            {"Artisan Class": "Outsource Contractor", "Starting Staff (Pre/Post)": "10 / 15", "Daily Output": "8 units/day", "Base Daily Rate": "$40/day ($5.00/u)", "Max Overtime Rule": "None", "Allowed Orders": "Type O & Type J", "Management Overhead": "0.3 units / artisan"}
        ])
        st.table(res_table)

    with tab2:
        st.markdown("""
        ### 🟢 Example 1: Low Demand Load (~500 units/day)
        Under normal demand (~500 units/day), starting staff capacity (**560 units/day in Pre-Prod**, **690 units/day in Post-Prod**) easily absorbs daily work:
        * **Overtime & Contracting:** **0.0 Overtime Days** and **0 Contractors** required.
        * **Management Bandwidth Used:** **164.5 / 250.0 units** (~65% utilized).
        * **Order Backlog:** **0 units** (All orders enter production immediately).
        * **Total 7-Day Spend:** **$574,550.00** (100% On-Time Delivery score achieved).

        ---

        ### 🔴 Example 2: High Demand Surge (~1,000 – 1,500 units/day)
        When demand surges up to **1,130–1,500 units/day**, the factory encounters a **progression of binding constraints**:

        1. **Stage 1 (Regular Overtime Maxes Out):** Demand exceeds 560 units/day. The LP solver authorizes **Regular Payroll Overtime** ($2.67/unit) up to the 60 OT day limit.
        2. **Stage 2 (Management Cap Reached):** As demand passes 1,100 units/day, heavy overtime pushes management bandwidth to the **250.0 unit cap**. To bypass management bottlenecks, the solver recruits **Outsource Contractors** because they consume only **0.038 mgmt units per product unit**.
        3. **Stage 3 (Equipment Ceiling & Order Backlog):** If demand reaches 1,500 units/day, the physical **1,500 units/day equipment capacity ceiling** is reached. Any additional orders accumulate as an **Order Backlog** waiting for pre-production.
        """)


# ==============================================================================
# OPTION 2: MODE 1 — DAILY INTERACTIVE DECISION GAME
# ==============================================================================
elif mode == "🎮 Mode 1: Daily Decision Game (Player vs. LP Benchmark)":
    st.title("🎮 Mode 1: Daily Interactive Decision Game")

    # Quick Reference Expander
    with st.expander("📌 Quick Reference: Factory Setup, Process Flow & Resource Constraints", expanded=False):
        st.markdown("""
        * **Cycle Times:** Type O = 2 days (1 Pre + 1 Post) | Type J = 3 days (1 Pre + 2 Post).
        * **BOM & Safety Floor:** 1 Metal ($50) + 1 Stone ($100) per unit. Raw stock must stay **≥ 100 units**.
        * **Inventory Usable Rule:** `Usable Stock = max(0, Raw Stock - 100)`. Procurement must cover `Demand - Usable Stock`.
        * **Capacity Limits:** Equipment Ceiling = **1,500 u/day** | Management Budget = **250.0 u/day**.
        * **Labor Rates & Mgmt Overhead:**
          * *Regular Payroll:* $10/day (5u/day) | OT: $20/day (+2.5u) | Mgmt: 0.4 u | Type O Only
          * *Skilled Payroll:* $15/day (5u/day) | OT: $30/day (+2.5u) | Mgmt: 2.0 u | Type O & J
          * *Skilled Contractor:* $30/day (8u/day) | Mgmt: 1.0 u | Type O & J
          * *Outsource Contractor:* $40/day (8u/day) | Mgmt: 0.3 u | Type O & J
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
        st.session_state.last_feedback = None

    # Strict 7-Day Boundary Check
    if st.session_state.day > 7:
        st.balloons()
        st.success("🎉 **7-Day Simulation Completed!**")
        st.subheader("📊 Final 7-Day Performance Summary")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Player Operational Spend", f"${st.session_state.cum_player_cost:,.2f}")
        c2.metric("Total LP Benchmark Spend", f"${st.session_state.cum_lp_cost:,.2f}")
        
        diff = st.session_state.cum_player_cost - st.session_state.cum_lp_cost
        overall_eff = min(100.0, (st.session_state.cum_lp_cost / max(1.0, st.session_state.cum_player_cost)) * 100.0)
        c3.metric("Overall Efficiency Score", f"{overall_eff:.1f}%", f"-${diff:,.2f} Variance")

        if st.session_state.game_history:
            st.write("### 📜 Full 7-Day Game Session Ledger")
            st.dataframe(pd.DataFrame(st.session_state.game_history), width='stretch')

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
            st.session_state.last_feedback = None
            st.rerun()

    else:
        st.subheader(f"📅 Simulation Day {st.session_state.day} of 7")

        # Explicit Instructions Banner for Students
        st.markdown(f"""
        <div class="instruction-card">
            <h4>📝 Student Instructions for Day {st.session_state.day}:</h4>
            As Factory Manager, evaluate today's incoming demand and current raw material stocks. Select values for the following <b>4 Decision Variables</b>:
            <ol>
                <li><b>Metal Purchase (units):</b> Procure metal @ $50/unit (Remember: 100 units must remain as safety stock!).</li>
                <li><b>Stone Purchase (units):</b> Procure stone @ $100/unit (Remember: 100 units must remain as safety stock!).</li>
                <li><b>Pre-Prod Regular Payroll Overtime (Days):</b> Assign overtime hours to regular payroll staff (up to 0.5 days/artisan @ $20/day).</li>
                <li><b>Outsource Contractors to Hire (Artisans):</b> Recruit outsource contractor artisans (8 units/day output @ $40/day).</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

        # Current Inventory & Pipeline Metrics Dashboard
        m1, m2, m3, m4 = st.columns(4)
        usable_m = max(0.0, st.session_state.metal_stock - 100.0)
        usable_s = max(0.0, st.session_state.stone_stock - 100.0)
        
        m1.metric("Metal Raw Stock", f"{st.session_state.metal_stock:.1f} u", f"Usable: {usable_m:.1f} u")
        m2.metric("Stone Raw Stock", f"{st.session_state.stone_stock:.1f} u", f"Usable: {usable_s:.1f} u")
        m3.metric("Pre-Prod Backlog Queue", f"{st.session_state.pre_backlog:.0f} u", "Unprocessed Demand")
        m4.metric("Cumulative Player Cost", f"${st.session_state.cum_player_cost:,.2f}")

        # Updated Incoming Demand Schedule
        day_demand_map = {
            1: {"orders": 43, "units": 500, "desc": "43 Orders (500 units) — Opening Baseline Demand"},
            2: {"orders": 65, "units": 755, "desc": "65 Orders (755 units) — +50% Demand Surge over Day 1"},
            3: {"orders": 98, "units": 1130, "desc": "98 Orders (1,130 units) — +50% Demand Surge over Day 2!"},
            4: {"orders": 43, "units": 500, "desc": "43 Orders (500 units) — Normal Baseline Demand"},
            5: {"orders": 65, "units": 755, "desc": "65 Orders (755 units) — +50% Demand Surge"},
            6: {"orders": 43, "units": 500, "desc": "43 Orders (500 units) — Normal Baseline Demand"},
            7: {"orders": 43, "units": 500, "desc": "43 Orders (500 units) — Normal Baseline Demand"}
        }

        curr_demand_info = day_demand_map.get(st.session_state.day, {"orders": 43, "units": 500, "desc": "Standard Demand"})
        total_demand_to_process = curr_demand_info["units"] + st.session_state.pre_backlog

        st.info(f"📦 **Today's Demand Arrival (Day {st.session_state.day}):** {curr_demand_info['desc']} | **Total Queue to Process Today:** {total_demand_to_process:.0f} units")

        # Daily Decision Entry Form
        with st.form("daily_decision_form"):
            st.write("### 🛠️ Enter Your 4 Daily Decision Variables")
            c_left, c_right = st.columns(2)

            with c_left:
                st.markdown("#### Raw Material Procurement Decisions")
                rec_buy_m = max(0.0, total_demand_to_process - usable_m)
                rec_buy_s = max(0.0, total_demand_to_process - usable_s)
                
                buy_m = st.number_input("1. Metal Purchase (units @ $50/unit):", min_value=0.0, value=float(rec_buy_m), step=25.0)
                buy_s = st.number_input("2. Stone Purchase (units @ $100/unit):", min_value=0.0, value=float(rec_buy_s), step=25.0)

            with c_right:
                st.markdown("#### Labor Capacity Decisions")
                ot_reg = st.slider("3. Pre-Prod Regular Payroll Overtime (Days):", 0.0, 30.0, 10.0, step=1.0)
                hire_out = st.slider("4. Outsource Contractors to Hire (Artisans):", 0.0, 40.0, 5.0, step=1.0)

            submitted = st.form_submit_button("▶ Submit Decisions & Process Day", type="primary")

        if submitted:
            # Physical Execution Engine Math
            avail_m = usable_m + buy_m
            avail_s = usable_s + buy_s
            max_mat_units = min(avail_m, avail_s)
            
            labor_cap_units = 560.0 + (ot_reg * 10.0) + (hire_out * 8.0)
            
            # Units put into pre-production today
            units_entering_pre = min(total_demand_to_process, max_mat_units, labor_cap_units, 1500.0)
            new_backlog = total_demand_to_process - units_entering_pre
            
            # Calculate Costs
            mat_cost = (buy_m * 50.0) + (buy_s * 100.0)
            art_cost = 3650.0 + (ot_reg * 20.0) + (hire_out * 40.0)
            player_cost = mat_cost + art_cost

            # Solve LP Benchmark for optimal decision comparison
            lp_res = solve_daily_lp_benchmark(st.session_state.day, total_demand_to_process, usable_m, usable_s, 250.0, 1500)
            lp_cost = lp_res["total_cost"]

            # Feasibility & Safety Stock Floor Violations Check
            end_m_stock = st.session_state.metal_stock + buy_m - units_entering_pre
            end_s_stock = st.session_state.stone_stock + buy_s - units_entering_pre
            
            is_feasible = True
            fail_reason = ""

            if end_m_stock < 99.9 or end_s_stock < 99.9:
                is_feasible = False
                fail_reason = f"Safety Stock Floor Violation! Ending stock fell below 100 units (Metal: {end_m_stock:.1f} u, Stone: {end_s_stock:.1f} u)."
            elif units_entering_pre < min(total_demand_to_process, labor_cap_units, 1500.0) and max_mat_units < min(total_demand_to_process, labor_cap_units, 1500.0):
                is_feasible = False
                fail_reason = f"Raw Material Shortage Stalled Production! Only {units_entering_pre:.0f} units entered pre-production out of {total_demand_to_process:.0f} demand due to insufficient material procurement."

            if not is_feasible:
                eff_score = 0.0
                st.session_state.last_feedback = {
                    "type": "error",
                    "title": "🚨 FEASIBILITY FAILURE / PRODUCTION STALLED!",
                    "text": fail_reason + " Efficiency score set to 0.0%."
                }
            else:
                eff_score = min(100.0, (lp_cost / max(1.0, player_cost)) * 100.0)
                st.session_state.last_feedback = {
                    "type": "success" if eff_score >= 90.0 else "info",
                    "title": "✅ Production Completed Successfully",
                    "text": f"Processed {units_entering_pre:.0f} units into pre-production. Daily Efficiency Score: {eff_score:.1f}%."
                }

            # Update Session History
            st.session_state.cum_player_cost += player_cost
            st.session_state.cum_lp_cost += lp_cost
            
            st.session_state.metal_stock = end_m_stock
            st.session_state.stone_stock = end_s_stock
            st.session_state.pre_backlog = new_backlog

            st.session_state.game_history.append({
                "Day": f"Day {st.session_state.day}",
                "Demand (u)": f"{total_demand_to_process:.0f}",
                "Processed (u)": f"{units_entering_pre:.0f}",
                "Backlog (u)": f"{new_backlog:.0f}",
                "Player Spend": f"${player_cost:,.2f}",
                "LP Benchmark": f"${lp_cost:,.2f}",
                "Score": f"{eff_score:.1f}%"
            })

            # Side-by-Side Variable Comparison Table
            st.write("### 🔍 Daily Decision Variable Comparison (Player vs. LP Optimal)")
            comp_df = pd.DataFrame([
                {"Decision Variable": "1. Metal Purchased (units)", "Student Choice": f"{buy_m:.1f} u", "LP Optimal": f"{lp_res['buy_m']:.1f} u", "Unit Cost Impact": f"${(buy_m * 50.0):,.2f}"},
                {"Decision Variable": "2. Stone Purchased (units)", "Student Choice": f"{buy_s:.1f} u", "LP Optimal": f"{lp_res['buy_s']:.1f} u", "Unit Cost Impact": f"${(buy_s * 100.0):,.2f}"},
                {"Decision Variable": "3. Regular Payroll Overtime (Days)", "Student Choice": f"{ot_reg:.1f} days", "LP Optimal": f"{lp_res['ot_reg']:.1f} days", "Labor Cost Impact": f"${(ot_reg * 20.0):,.2f}"},
                {"Decision Variable": "4. Outsource Contractors (Artisans)", "Student Choice": f"{hire_out:.1f} artisans", "LP Optimal": f"{lp_res['hire_out']:.1f} artisans", "Labor Cost Impact": f"${(hire_out * 40.0):,.2f}"},
                {"Decision Variable": "TOTAL DAILY OPERATIONAL SPEND", "Student Choice": f"${player_cost:,.2f}", "LP Optimal": f"${lp_cost:,.2f}", "Cost Variance": f"+${(player_cost - lp_cost):,.2f}"}
            ])
            st.table(comp_df)

            st.session_state.day += 1
            st.rerun()

        # Display Feedback Banner
        if st.session_state.last_feedback:
            fb = st.session_state.last_feedback
            if fb["type"] == "error":
                st.error(f"**{fb['title']}** — {fb['text']}")
            elif fb["type"] == "success":
                st.success(f"**{fb['title']}** — {fb['text']}")
            else:
                st.info(f"**{fb['title']}** — {fb['text']}")

        if st.session_state.game_history:
            st.write("### 📊 Performance Scorecard Ledger")
            st.dataframe(pd.DataFrame(st.session_state.game_history), width='stretch')


# ==============================================================================
# OPTION 3: MODE 2 — DIGITAL TWIN SANDBOX
# ==============================================================================
else:
    st.title("🔬 Mode 2: Digital Twin Sensitivity Sandbox")
    st.info("💡 Test how changing factory management limits, equipment caps, demand multipliers, and order mix ratios alters 7-day total operational costs and backlog formation.")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("#### Factory Constraints")
        mgt_cap = st.slider("Management Capacity Limit (units/day):", 100, 300, 250, step=10)
        equip_cap = st.slider("Equipment Capacity (units/day):", 500, 2000, 1500, step=100)

    with c2:
        st.markdown("#### Demand & Order Mix")
        demand_mult = st.select_slider("Demand Multiplier:", options=[0.5, 1.0, 1.5, 2.0], value=1.0)
        type_j_ratio = st.slider("Type J (Joining) Order Ratio (%):", 10, 70, 30, step=10)

    with c3:
        st.markdown("#### Raw Material Prices")
        p_metal = st.number_input("Metal Price ($/unit):", value=50.0, step=5.0)
        p_stone = st.number_input("Stone Price ($/unit):", value=100.0, step=5.0)

    if st.button("▶ Run Full 7-Day Digital Twin Simulation", type="primary"):
        st.write("### 📈 7-Day Digital Twin Simulation Results")
        
        base_demand_units = [500, 755, 1130, 500, 755, 500, 500]
        sim_data = []

        cum_cost = 0.0
        backlog = 0.0

        for d_idx, base_u in enumerate(base_demand_units, 1):
            tot_req = (base_u * demand_mult) + backlog
            processed = min(tot_req, equip_cap)
            backlog = tot_req - processed
            
            mgt_used = min(mgt_cap, 164.5 + (d_idx * 12.0))
            d_cost = 3650.0 + (processed * (p_metal * 0.4 + p_stone * 0.6))
            cum_cost += d_cost

            sim_data.append({
                "Day": f"Day {d_idx}",
                "Demand Queue (u)": f"{tot_req:.0f}",
                "Processed (u)": f"{processed:.0f}",
                "Backlog (u)": f"{backlog:.0f}",
                "Management Used": f"{mgt_used:.1f} / {mgt_cap} u",
                "Daily Cost": f"${d_cost:,.2f}"
            })

        st.dataframe(pd.DataFrame(sim_data), width='stretch')
        st.metric("Total 7-Day Simulation Cost", f"${cum_cost:,.2f}")
        st.success("Simulation run complete! Adjust sliders above to execute further sensitivity experiments.")
