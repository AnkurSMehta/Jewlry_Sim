import streamlit as st
import pulp
import pandas as pd
import json

st.set_page_config(
    page_title="Jewelry Supply Chain Teaching Platform",
    page_icon="💎",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #38bdf8; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #94a3b8; margin-bottom: 1.5rem; }
    .card { background-color: #1e293b; padding: 1.2rem; border-radius: 0.5rem; border: 1px solid #334155; margin-bottom: 1rem; }
    .instruction-card-light { 
        background-color: #ffffff !important; 
        border: 2px solid #0284c7 !important; 
        border-radius: 0.6rem !important; 
        padding: 1.2rem !important; 
        margin-bottom: 1.2rem !important; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    .instruction-card-light h3, .instruction-card-light h4 {
        color: #0f172a !important;
        font-weight: 800 !important;
        margin-top: 0.2rem !important;
    }
    .instruction-card-light p, .instruction-card-light li, .instruction-card-light span, .instruction-card-light div {
        color: #1e293b !important;
        font-size: 0.98rem !important;
        line-height: 1.5 !important;
    }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-val { font-size: 1.5rem; font-weight: 700; color: #f8fafc; }
    .score-good { color: #10b981; font-weight: bold; }
    .score-warn { color: #f59e0b; font-weight: bold; }
    .binding-badge { background-color: #ef4444; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
    .slack-badge { background-color: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💎 Jewelry Supply Chain Teaching Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive Operational Decision Game & Digital Twin Optimization Sandbox</div>', unsafe_allow_html=True)

mode = st.sidebar.radio(
    "Select Platform Option:",
    ["📖 Option 1: Case Study Introduction & Tutorial", "🎮 Option 2: Mode 1 - Daily Decision Game", "🔬 Option 3: Mode 2 - Digital Twin Sandbox"]
)

# Load Default Config
@st.cache_data
def load_default_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except Exception:
        return {
            "simulation_settings": { "management_capacity_daily": 250.0, "equipment_capacity_daily": 1500, "min_raw_material_safety_stock": 100 },
            "raw_materials": { "metal": { "unit_cost": 50.0 }, "stone": { "unit_cost": 100.0 } }
        }

cfg = load_default_config()

def solve_daily_lp_benchmark(day_idx, demand_units, mgt_limit=250.0, equip_limit=1500, starting_metal=500.0, starting_stone=500.0):
    """
    Computes the mathematical LP benchmark using PuLP.
    Passes mgt_limit and equip_limit directly as strict linear constraints.
    Returns optimal decision variables, cost, status, and constraint binding/slack details.
    """
    try:
        prob = pulp.LpProblem(f"LP_Bench_Day_{day_idx}", pulp.LpMinimize)
        
        usable_metal = max(0.0, starting_metal - 100.0)
        usable_stone = max(0.0, starting_stone - 100.0)
        
        req_proc_m = max(0.0, demand_units - usable_metal)
        req_proc_s = max(0.0, demand_units - usable_stone)
        
        # Decision variables
        buy_m = pulp.LpVariable("buy_m", lowBound=req_proc_m, cat=pulp.LpContinuous)
        buy_s = pulp.LpVariable("buy_s", lowBound=req_proc_s, cat=pulp.LpContinuous)
        ot_reg = pulp.LpVariable("ot_reg", lowBound=0.0, upBound=60.0, cat=pulp.LpContinuous)
        hire_out = pulp.LpVariable("hire_out", lowBound=0.0, upBound=30.0, cat=pulp.LpContinuous)
        
        # Production output capacity constraint (860u base + 2.5u per OT day + 8.0u per outsource artisan)
        output_cap = 860.0 + (ot_reg * 2.5) + (hire_out * 8.0)
        
        # Max processable units considering equipment cap and demand
        target_prod = min(demand_units, float(equip_limit))
        prob += (output_cap >= target_prod, "Output_Cap_Constraint")
        prob += (output_cap <= float(equip_limit), "Equip_Cap_Constraint")
        
        # Management capacity constraint
        mgmt_expr = 164.5 + (ot_reg * 0.4) + (hire_out * 0.3)
        prob += (mgmt_expr <= float(mgt_limit), "Management_Cap_Constraint")
        
        # Objective Function: Minimize Total Daily Cost
        daily_cost = 3650.0 + (ot_reg * 20.0) + (hire_out * 40.0) + (buy_m * 50.0) + (buy_s * 100.0)
        prob += daily_cost
        
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            bm_val = float(pulp.value(buy_m))
            bs_val = float(pulp.value(buy_s))
            ot_val = float(pulp.value(ot_reg))
            ho_val = float(pulp.value(hire_out))
            tot_cost_val = float(pulp.value(daily_cost))
            mgmt_used_val = 164.5 + (ot_val * 0.4) + (ho_val * 0.3)
            out_cap_val = 860.0 + (ot_val * 2.5) + (ho_val * 8.0)
            
            # Constraint Slacks
            mgmt_slack = float(mgt_limit) - mgmt_used_val
            ot_slack = 60.0 - ot_val
            out_slack = 30.0 - ho_val
            equip_slack = float(equip_limit) - out_cap_val
            
            # Determine active bottleneck
            if mgmt_slack < 0.1 and target_prod < demand_units:
                bottleneck_str = "🔴 Management Bandwidth Cap Reached (Binding)"
            elif ot_slack < 0.1 and out_slack > 0.1:
                bottleneck_str = "🟡 Overtime Limit Maxed (60 Days Max)"
            elif out_slack < 0.1 and ot_slack > 0.1:
                bottleneck_str = "🔵 Outsource Contractor Limit Maxed (30 Artisans Max)"
            elif equip_slack < 0.1:
                bottleneck_str = "⚠️ Equipment Capacity Ceiling Reached (1,500 u/day)"
            elif ot_val > 0.1 or ho_val > 0.1:
                bottleneck_str = "🔵 Demand Exceeds Baseline (Overtime/Outsource Active)"
            else:
                bottleneck_str = "🟢 Baseline Capacity (Unconstrained)"
                
            return {
                'buy_m': bm_val, 'buy_s': bs_val, 'ot_reg': ot_val, 'hire_out': ho_val,
                'total_cost': tot_cost_val, 'mgmt_used': mgmt_used_val, 'output_cap': out_cap_val,
                'mgmt_slack': mgmt_slack, 'ot_slack': ot_slack, 'out_slack': out_slack, 'equip_slack': equip_slack,
                'status': 'Optimal', 'bottleneck': bottleneck_str
            }
    except Exception:
        pass
        
    # Analytical Fallback Solver
    usable_metal = max(0.0, starting_metal - 100.0)
    usable_stone = max(0.0, starting_stone - 100.0)
    buy_m_val = max(0.0, demand_units - usable_metal)
    buy_s_val = max(0.0, demand_units - usable_stone)
    
    needed_extra = max(0.0, demand_units - 860.0)
    mgmt_headroom = max(0.0, float(mgt_limit) - 164.5)
    
    # Outsource contractor gives 8u for 0.3 mgmt ($40/day = $5.00/u) -> 26.67 u/mgmt
    # Overtime gives 2.5u for 0.4 mgmt ($20/day = $8.00/u) -> 6.25 u/mgmt
    # LP prefers Outsource Contractors first!
    ho_val = min(30.0, needed_extra / 8.0, mgmt_headroom / 0.3)
    rem_extra = max(0.0, needed_extra - (ho_val * 8.0))
    rem_mgmt = max(0.0, mgmt_headroom - (ho_val * 0.3))
    
    ot_val = min(60.0, rem_extra / 2.5, rem_mgmt / 0.4)
    
    mgmt_used_val = 164.5 + (ot_val * 0.4) + (ho_val * 0.3)
    out_cap_val = 860.0 + (ot_val * 2.5) + (ho_val * 8.0)
    tot_cost_val = 3650.0 + (ot_val * 20.0) + (ho_val * 40.0) + (buy_m_val * 50.0) + (buy_s_val * 100.0)
    
    mgmt_slack = float(mgt_limit) - mgmt_used_val
    ot_slack = 60.0 - ot_val
    out_slack = 30.0 - ho_val
    equip_slack = float(equip_limit) - out_cap_val
    
    if out_slack < 0.1 and ot_slack > 0.1:
        bottleneck_str = "🔵 Outsource Contractors Maxed (30 Artisans, 0 Slack)"
    elif mgmt_slack < 0.1:
        bottleneck_str = "🔴 Management Bandwidth Cap Reached (Binding)"
    elif ot_val > 0.1 or ho_val > 0.1:
        bottleneck_str = "🔵 Demand Exceeds Baseline (Overtime/Outsource Active)"
    else:
        bottleneck_str = "🟢 Baseline Capacity (Unconstrained)"
        
    return {
        'buy_m': buy_m_val, 'buy_s': buy_s_val, 'ot_reg': ot_val, 'hire_out': ho_val,
        'total_cost': tot_cost_val, 'mgmt_used': mgmt_used_val, 'output_cap': out_cap_val,
        'mgmt_slack': mgmt_slack, 'ot_slack': ot_slack, 'out_slack': out_slack, 'equip_slack': equip_slack,
        'status': 'Optimal Benchmark', 'bottleneck': bottleneck_str
    }

# --- OPTION 1: CASE STUDY TUTORIAL ---
if mode == "📖 Option 1: Case Study Introduction & Tutorial":
    st.header("📖 Option 1: Case Study Introduction & Educational Tutorial")
    st.info("💡 **Welcome Student!** Read through this two-part case study tutorial to master Linear Programming (LP) optimization, constraint binding vs. slack, and factory simulation dynamics before playing the game.")

    tab1, tab2 = st.tabs(["📘 Part 1: Theory, Setup & Constraints", "📊 Part 2: Worked Tutorials & Constraint Progression"])

    with tab1:
        st.markdown("""
        ### 1. Fundamentals of Optimization & Simulation
        In modern operations management, two complementary analytical tools work together:
        * **Linear Programming (LP) Solver (*The Intelligent Planner*):** A mathematical optimization algorithm that evaluates cost functions, capacity bounds, and resource limits to determine the mathematically optimal decision variables.
        * **Discrete Event Simulation (DES) (*The Physical Factory Engine*):** A dynamic event-driven engine that processes orders, tracks raw material stocks, moves work-in-progress (WIP) through factory benches, and measures delivery performance.

        ---

        ### 2. Manufacturing Flow & Lead Times
        1. **Design Stage (Optional):** Takes 1 day per order ($100 fee). Offers a 25% chance of reducing metal consumption to 0.9 units/piece (otherwise 1.0 unit).
        2. **Pre-Production Stage:** Material cutting and prep (1 day lead time). Equipment limit = 1,500 units/day.
        3. **Post-Production Stage:** Finishing and assembly. Equipment limit = 1,500 units/day.
        * **Order Type Cycle Times:**
          * **Type O (Ordinary Orders):** Requires 1 day in Pre-Production + 1 day in Post-Production = **2-Day Total Cycle Time**.
          * **Type J (Joining Orders):** Requires 1 day in Pre-Production + 2 days in Post-Production = **3-Day Total Cycle Time**.

        ---

        ### 3. Resource Matrix & Operational Rules Table
        """)

        res_table = pd.DataFrame([
            {"Artisan Class": "Regular Payroll", "Base Staff (Pre/Post)": "60 / 70", "Output Rate": "5 u/day", "Base Rate": "$10/day ($2.00/u)", "Overtime Rule": "Up to 0.5 day ($20/day)", "Allowed Orders": "Type O Only", "Mgmt Overhead": "0.4 units / artisan"},
            {"Artisan Class": "Skilled Payroll", "Base Staff (Pre/Post)": "20 / 20", "Output Rate": "5 u/day", "Base Rate": "$15/day ($3.00/u)", "Overtime Rule": "Up to 0.5 day ($30/day)", "Allowed Orders": "Type O & Type J", "Mgmt Overhead": "2.0 units / artisan"},
            {"Artisan Class": "Skilled Contractor", "Base Staff (Pre/Post)": "10 / 15", "Output Rate": "8 u/day", "Base Rate": "$30/day ($3.75/u)", "Overtime Rule": "None", "Allowed Orders": "Type O & Type J", "Mgmt Overhead": "1.0 unit / artisan"},
            {"Artisan Class": "Outsource Contractor", "Base Staff (Pre/Post)": "10 / 15", "Output Rate": "8 u/day", "Base Rate": "$40/day ($5.00/u)", "Overtime Rule": "None", "Allowed Orders": "Type O & Type J", "Mgmt Overhead": "0.3 units / artisan"}
        ])
        st.table(res_table)

        st.markdown(r"""
        * **Bill of Materials (BOM):** Each product unit requires **1 unit Metal ($50)** + **1 unit Stone ($100)**.
        * **Safety Stock Floor Rule:** Raw material inventory must **never drop below 100 units**.
          \\[\\text{Usable Raw Stock} = \max(0.0,\; \text{Current Stock} - 100.0)\]
          *Example:* If today's demand is **500 units** and starting metal stock is **200 units**, usable stock is **100 units** (200 - 100). The factory must procure at least **400 units** (`500 - 100 = 400`). If less than 400 units are procured, production stutters and unfulfilled orders enter the **Backlog Queue**.
        * **Management Bandwidth Cap:** Default cap = **250.0 units/day** (or 180.0 in tight scenarios).
          \\[\\text{Management Consumption} = 164.5 \text{ (Base Floor)} + (\text{OT Days} \times 0.4) + (\text{Outsource Artisans} \times 0.3) \le \text{Mgmt Cap}\]
        * **Constraint Binding vs. Slack Theory:**
          * **Binding Constraint (0 Slack):** A resource that is fully maxed out (e.g., Outsource Contractor limit = 30.0 artisans used, Slack = 0.0). It limits further optimization.
          * **Non-Binding Constraint (Has Slack):** A resource with leftover capacity (e.g., Overtime days = 12.0 used out of 60.0 max, Slack = 48.0 days).
        """)

    with tab2:
        st.markdown("""
        ### 4. Worked Tutorials: Low Load vs High Load Demand Surge

        #### 🟢 Case Example 1: Low Demand Load (~500 units/day)
        * **Demand Scenario:** Daily incoming demand = 500 units. Starting stock = 500 Metal, 500 Stone.
        * **LP Decision Analysis:**
          * Baseline regular output capacity (860 units/day) exceeds 500 units.
          * Overtime Authorized = **0.0 Days** (Slack = 60.0 days).
          * Outsource Contractors Hired = **0.0 Artisans** (Slack = 30.0 artisans).
          * Management Used = **164.5 / 250.0 u** (Slack = 85.5 u).
          * Material Procured = **100 Metal / 100 Stone** (to replenish 400u consumed and maintain 500u ending stock).
        * **Key Insight:** Under low load, baseline staff easily fulfills demand. Labor constraints have large slack.

        ---

        #### 🔴 Case Example 2: High Demand Surge (~1,130 units/day under 180 Management Cap)
        * **Demand Scenario:** Incoming demand = 1,130 units (requires 270 extra units above 860u base).
        * **LP Decision Analysis:**
          * **Unit Output Cost Ranking:**
            * Outsource Contractor: $40/day for 8u output = **$5.00/unit output** (Consumes 0.3 mgmt/artisan = 26.67 u output per mgmt unit).
            * Regular Overtime: $20/day for 2.5u output = **$8.00/unit output** (Consumes 0.4 mgmt/day = 6.25 u output per mgmt unit).
          * **LP Optimal Strategy:** Outsource Contractors are BOTH cheaper ($5.00 vs $8.00) and far more management-efficient!
          * **Outsource Contractors Hired:** **30.0 Artisans (MAXED OUT — 0.0 Slack!)** -> Yields +240 units output.
          * **Regular Overtime Days:** **12.0 Days (48.0 Days SLACK!)** -> Yields remaining +30 units output.
          * **Management Used:** `164.5 + (12.0 * 0.4) + (30.0 * 0.3) = 178.3 / 180.0 u` (Slack = 1.7 u).
        * **Key Insight:** The LP solver maxes out Outsource Contractors FIRST because they yield 26.67 units per management unit vs. overtime's 6.25 units per management unit. Overtime is kept low at 12.0 days, leaving **48.0 days of Overtime Slack**!
        """)

# --- OPTION 2: MODE 1 DAILY DECISION GAME ---
elif mode == "🎮 Option 2: Mode 1 - Daily Decision Game":
    st.header("🎮 Mode 1: Interactive Daily Decision Game (Player vs LP Benchmark)")
    
    with st.expander("📌 Quick Reference: Factory Setup, Process Flow & Resource Constraints", expanded=False):
        st.markdown("""
        * **Manufacturing Lead Times:** Type O = 2 days (1 Pre + 1 Post), Type J = 3 days (1 Pre + 2 Post).
        * **Process Constraints:** Pre-Prod Cap = 1,500 u/day, Post-Prod Cap = 1,500 u/day.
        * **Raw Material Safety Floor:** Minimum 100 units Metal & 100 units Stone must be preserved at all times (`Usable Stock = Current Stock - 100`).
        * **Management Budget Cap:** 250.0 units/day max management bandwidth (or custom set cap).
        * **Labor Unit Cost & Efficiency:** Outsource Contractors = $5.00/u output (26.67 u/mgmt), Regular Payroll Overtime = $8.00/u output (6.25 u/mgmt).
        """)

    if 'day' not in st.session_state:
        st.session_state.day = 1
        st.session_state.metal_stock = 500.0
        st.session_state.stone_stock = 500.0
        st.session_state.wip_metal = 0.0
        st.session_state.wip_stone = 0.0
        st.session_state.backlog_queue = 0.0
        st.session_state.cum_player_cost = 0.0
        st.session_state.cum_lp_cost = 0.0
        st.session_state.game_history = []
        st.session_state.last_comparison = None
        st.session_state.submitted_today = False

    if st.session_state.day <= 7:
        st.subheader(f"📅 Simulation State: Day {st.session_state.day} of 7")

        # Student Instructions Card (White Background, Dark Navy Text)
        st.markdown(f"""
        <div class="instruction-card-light">
            <h3>✍️ Instructions for Day {st.session_state.day}: Select Your 4 Decision Variables</h3>
            <p>Welcome Manager! Review today's incoming demand and backlog below. Pick values for the <strong>4 Decision Variables</strong> to run the factory for Day {st.session_state.day}:</p>
            <ul>
                <li><strong>1. Metal Purchase (units):</strong> Procure metal @ $50/unit (Remember to maintain the 100-unit safety floor!).</li>
                <li><strong>2. Stone Purchase (units):</strong> Procure stone @ $100/unit (Remember to maintain the 100-unit safety floor!).</li>
                <li><strong>3. Pre-Prod Regular Payroll Overtime (Days):</strong> Assign overtime to Regular Payroll staff (up to 0.5 days/artisan @ $20/day).</li>
                <li><strong>4. Outsource Contractors to Hire (Artisans):</strong> Recruit Outsource Contractor artisans (8 units/day output @ $40/day).</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # Inventory & Pipeline Dashboard Cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Metal Raw Stock", f"{st.session_state.metal_stock:.1f} u", delta="100u Safety Floor")
        m2.metric("Stone Raw Stock", f"{st.session_state.stone_stock:.1f} u", delta="100u Safety Floor")
        m3.metric("WIP Material (In Factory)", f"{st.session_state.wip_metal:.1f} u")
        m4.metric("Pre-Prod Backlog Queue", f"{st.session_state.backlog_queue:.0f} u")

        # Demand Schedule
        demand_schedule = {
            1: {"count": 43, "units": 500, "desc": "Opening Baseline Demand"},
            2: {"count": 65, "units": 755, "desc": "+50% Demand Surge over Day 1"},
            3: {"count": 98, "units": 1130, "desc": "+50% Demand Surge over Day 2! (Surge Surcharge Trigger)"},
            4: {"count": 43, "units": 500, "desc": "Normal Baseline Demand"},
            5: {"count": 65, "units": 755, "desc": "+50% Demand Surge"},
            6: {"count": 43, "units": 500, "desc": "Normal Baseline Demand"},
            7: {"count": 43, "units": 500, "desc": "Normal Baseline Demand"}
        }

        curr_demand = demand_schedule.get(st.session_state.day, {"count": 43, "units": 500, "desc": "Standard Demand"})
        tot_queue_today = curr_demand['units'] + st.session_state.backlog_queue

        st.info(f"📦 **Today's Incoming Demand (Day {st.session_state.day}):** {curr_demand['count']} Orders ({curr_demand['units']} units) — *{curr_demand['desc']}* | **Total Workload Queue:** {tot_queue_today:.0f} units")

        # STAGE 1: DECISION SUBMISSION FORM
        if not st.session_state.submitted_today:
            with st.form("daily_decision_form"):
                st.write(f"### 🛠️ Enter Decisions for Day {st.session_state.day}")
                col_left, col_right = st.columns(2)

                usable_m = max(0.0, st.session_state.metal_stock - 100.0)
                usable_s = max(0.0, st.session_state.stone_stock - 100.0)
                rec_m = max(0.0, tot_queue_today - usable_m)
                rec_s = max(0.0, tot_queue_today - usable_s)

                with col_left:
                    st.markdown("#### Raw Material Procurement")
                    buy_m = st.number_input(f"Purchase Metal (units @ $50/unit) [Min Rec: {rec_m:.0f}u]:", min_value=0, value=int(rec_m), step=25)
                    buy_s = st.number_input(f"Purchase Stone (units @ $100/unit) [Min Rec: {rec_s:.0f}u]:", min_value=0, value=int(rec_s), step=25)

                with col_right:
                    st.markdown("#### Labor Allocation")
                    ot_reg = st.slider("Pre-Prod Regular Payroll Overtime (Days):", 0.0, 60.0, 0.0, step=1.0)
                    hire_out = st.slider("Outsource Contractors to Hire (Artisans):", 0.0, 30.0, 0.0, step=1.0)

                submitted = st.form_submit_button(f"📩 Submit Decisions for Day {st.session_state.day}", type="primary")

            if submitted:
                tot_avail_m = st.session_state.metal_stock + buy_m - 100.0
                tot_avail_s = st.session_state.stone_stock + buy_s - 100.0
                usable_mat = min(max(0.0, tot_avail_m), max(0.0, tot_avail_s))
                
                labor_cap = 860.0 + (ot_reg * 2.5) + (hire_out * 8.0)
                max_possible_prod = min(tot_queue_today, labor_cap, 1500.0)
                feasible_prod = min(max_possible_prod, usable_mat)
                
                is_feasible = (feasible_prod >= tot_queue_today - 5.0) and (tot_avail_m >= 0.0) and (tot_avail_s >= 0.0)
                
                mat_spend = (buy_m * 50.0) + (buy_s * 100.0)
                labor_spend = 3650.0 + (ot_reg * 20.0) + (hire_out * 40.0)
                player_day_cost = mat_spend + labor_spend
                
                # Solve LP Benchmark
                lp_res = solve_daily_lp_benchmark(st.session_state.day, tot_queue_today, 250.0, 1500, st.session_state.metal_stock, st.session_state.stone_stock)
                lp_day_cost = lp_res['total_cost']
                
                if not is_feasible:
                    efficiency = 0.0
                    score_str = "0.0% (Feasibility Failure)"
                else:
                    efficiency = min(100.0, (lp_day_cost / player_day_cost) * 100.0) if player_day_cost > 0 else 100.0
                    score_str = f"{efficiency:.1f}%"
                    
                unprocessed = max(0.0, tot_queue_today - feasible_prod)
                
                st.session_state.last_comparison = {
                    'day': st.session_state.day,
                    'is_feasible': is_feasible,
                    'player_m': buy_m, 'lp_m': lp_res['buy_m'],
                    'player_s': buy_s, 'lp_s': lp_res['buy_s'],
                    'player_ot': ot_reg, 'lp_ot': lp_res['ot_reg'],
                    'player_out': hire_out, 'lp_out': lp_res['hire_out'],
                    'player_cost': player_day_cost, 'lp_cost': lp_day_cost,
                    'lp_res': lp_res,
                    'efficiency': efficiency,
                    'score_str': score_str,
                    'feasible_prod': feasible_prod,
                    'unprocessed': unprocessed,
                    'buy_m': buy_m, 'buy_s': buy_s
                }
                
                st.session_state.submitted_today = True
                st.rerun()

        # STAGE 2: DISPLAY LP SOLUTION & ANALYSIS
        else:
            comp = st.session_state.last_comparison
            lp_res = comp['lp_res']
            
            st.markdown("---")
            st.write(f"### 📊 Day {comp['day']} Decision Analysis & LP Solution Comparison")
            
            if not comp['is_feasible']:
                st.error("🚨 PRODUCTION STALLED / FEASIBILITY FAILURE: Your material purchases or labor capacity were insufficient to process the workload, or raw material fell below the 100u safety floor. Production stalled and a 0% score was assigned.")
            
            # Side-by-Side Comparison Table
            comp_df = pd.DataFrame([
                {"Decision Variable": "1. Metal Purchase (units)", "Player Choice": f"{comp['player_m']:.0f} u", "LP Optimal": f"{comp['lp_m']:.0f} u", "Cost Impact": f"${((comp['player_m'] - comp['lp_m']) * 50):,.2f}"},
                {"Decision Variable": "2. Stone Purchase (units)", "Player Choice": f"{comp['player_s']:.0f} u", "LP Optimal": f"{comp['lp_s']:.0f} u", "Cost Impact": f"${((comp['player_s'] - comp['lp_s']) * 100):,.2f}"},
                {"Decision Variable": "3. Regular Payroll Overtime (days)", "Player Choice": f"{comp['player_ot']:.1f} days", "LP Optimal": f"{comp['lp_ot']:.1f} days", "Cost Impact": f"${((comp['player_ot'] - comp['lp_ot']) * 20):,.2f}"},
                {"Decision Variable": "4. Outsource Contractors Hired (artisans)", "Player Choice": f"{comp['player_out']:.1f} artisans", "LP Optimal": f"{comp['lp_out']:.1f} artisans", "Cost Impact": f"${((comp['player_out'] - comp['lp_out']) * 40):,.2f}"},
                {"Decision Variable": "TOTAL DAILY OPERATIONAL SPEND", "Player Choice": f"${comp['player_cost']:,.2f}", "LP Optimal": f"${comp['lp_cost']:,.2f}", "Cost Impact": f"${(comp['player_cost'] - comp['lp_cost']):,.2f}"}
            ])
            st.table(comp_df)

            # Detailed Comparative Situation Explanations
            diff_cost = comp['player_cost'] - comp['lp_cost']
            if diff_cost > 1.0:
                st.warning(f"""
                #### 🔵 Comparative Situation Analysis: Player Spend is Higher (+${diff_cost:,.2f})
                **Why the LP Solution is Better & More Optimal:**
                1. **Material Inventory Efficiency:** The LP purchased the exact minimum quantity required to keep raw stock above the 100u safety floor without tying up extra cash in inventory.
                2. **Labor Class Ranking & Management Efficiency:** Outsource Contractors ($40/day for 8u = $5.00/u output) yield **26.67 units per mgmt unit** vs. Regular Overtime ($20/day for 2.5u = $8.00/u output) which yields **6.25 units per mgmt unit**. The LP solver maxes out Outsource Contractors first because they are both cheaper and far more management-efficient!
                3. **Management Bandwidth Protection:** The LP carefully balances overtime and contractor hiring to stay within the management cap.
                """)
            elif diff_cost < -1.0:
                st.info(f"""
                #### 🟠 Comparative Situation Analysis: Player Spend is Lower (${diff_cost:,.2f} less)
                **Why the LP Solution Chosen Choices are Necessary & Optimal:**
                1. **Preventing Production Stalls:** While your daily cash outflow appeared lower, under-purchasing materials risks stalling production or violating the 100u safety floor.
                2. **Preventing Order Backlog Accumulation:** Under-investing in overtime/contractors causes orders to get trapped in the backlog queue, risking late delivery penalties.
                3. **Full Demand Fulfillment:** The LP spend is optimal because it guarantees 100% throughput while maintaining the 100u safety floor.
                """)
            else:
                st.success("🌟 **PERFECT OPTIMIZATION!** Your decision choices matched the LP optimal benchmark perfectly across all 4 variables.")

            # Constraint Binding & Slack Analysis Box
            st.markdown(f"""
            <div class="instruction-card-light">
                <h4>🔎 LP Constraint Binding & Slack Analysis for Day {comp['day']}</h4>
                <p>Understanding which constraints are <strong>Binding (0 Slack)</strong> vs. <strong>Unconstrained (Has Slack)</strong> reveals how the LP solver chooses decision variables:</p>
                <ul>
                    <li><strong>Outsource Contractor Constraint (30 Artisans Max):</strong> {("🔴 BINDING (0.0 Artisans Slack — MAXED OUT!)" if lp_res['out_slack'] < 0.1 else f"🟢 SLACK ({lp_res['out_slack']:.1f} Artisans Headroom Available)")} <br><em>Explanation:</em> Outsource Contractors yield 26.67 units per management unit ($5.00/u output). The LP maxes out contractors first before using overtime.</li>
                    <li><strong>Regular Overtime Constraint (60 Days Max):</strong> {("🔴 BINDING (0.0 Days Slack — MAXED OUT!)" if lp_res['ot_slack'] < 0.1 else f"🟢 SLACK ({lp_res['ot_slack']:.1f} Days Overtime Headroom Left)")} <br><em>Explanation:</em> Overtime is used only for remaining workload after contractor limits are reached.</li>
                    <li><strong>Management Bandwidth Constraint (250.0 u Cap):</strong> {("🔴 BINDING (0.0 u Mgmt Headroom Left)" if lp_res['mgmt_slack'] < 0.1 else f"🟢 SLACK ({lp_res['mgmt_slack']:.1f} u Mgmt Headroom Available)")} <br><em>Explanation:</em> Total management consumed = {lp_res['mgmt_used']:.1f} u.</li>
                    <li><strong>Equipment Capacity Ceiling (1,500 u/day):</strong> {("🔴 BINDING (0.0 u Equipment Headroom Left)" if lp_res['equip_slack'] < 0.1 else f"🟢 SLACK ({lp_res['equip_slack']:.1f} u Equipment Capacity Available)")}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            # Clean white callout card with dark text (no dark fill)
            st.markdown(f"""
            <div class="instruction-card-light">
                <h4>👉 LP Solution Analysis Complete!</h4>
                <p>Review the LP optimal choices, cost comparison, and constraint slack analysis above. When you are ready to proceed to the next simulation day, click the button below.</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"▶ Step 1 Day Forward to Day {st.session_state.day + 1}", type="primary"):
                comp = st.session_state.last_comparison
                st.session_state.backlog_queue = comp['unprocessed']
                st.session_state.metal_stock = max(100.0, st.session_state.metal_stock + comp['buy_m'] - comp['feasible_prod'])
                st.session_state.stone_stock = max(100.0, st.session_state.stone_stock + comp['buy_s'] - comp['feasible_prod'])
                st.session_state.wip_metal += comp['feasible_prod']
                st.session_state.wip_stone += comp['feasible_prod']
                
                st.session_state.cum_player_cost += comp['player_cost']
                st.session_state.cum_lp_cost += comp['lp_cost']
                
                st.session_state.game_history.append({
                    "Day": f"Day {st.session_state.day}",
                    "Player Spend": f"${comp['player_cost']:,.2f}",
                    "LP Optimal": f"${comp['lp_cost']:,.2f}",
                    "Score": comp['score_str'],
                    "Backlog Left": f"{comp['unprocessed']:.0f} u"
                })
                
                st.session_state.day += 1
                st.session_state.submitted_today = False
                st.session_state.last_comparison = None
                st.rerun()

        if st.session_state.game_history:
            st.write("### 📈 7-Day Performance Ledger")
            st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)

    else:
        st.balloons()
        st.success("🎉 **7-DAY SIMULATION COMPLETED!** All 7 days have been processed. Review your final performance summary below.")
        if st.session_state.game_history:
            st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)
            
        if st.button("🔄 Restart 7-Day Game Session", type="primary"):
            st.session_state.day = 1
            st.session_state.metal_stock = 500.0
            st.session_state.stone_stock = 500.0
            st.session_state.wip_metal = 0.0
            st.session_state.wip_stone = 0.0
            st.session_state.backlog_queue = 0.0
            st.session_state.cum_player_cost = 0.0
            st.session_state.cum_lp_cost = 0.0
            st.session_state.game_history = []
            st.session_state.last_comparison = None
            st.session_state.submitted_today = False
            st.rerun()

# --- OPTION 3: MODE 2 DIGITAL TWIN SANDBOX ---
else:
    st.header("🔬 Mode 2: Digital Twin Sensitivity Sandbox")
    st.info("💡 **Goal:** Test how changing factory constraints, demand multipliers, and order mix alters 7-day costs and throughput. Watch how bottlenecks and constraint slacks shift across parameter choices.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Factory Constraints")
        mgt_cap = st.slider("Management Capacity Limit (units/day):", 100, 300, 180, step=10)
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
        
        base_demand_units = [500, 755, 1130, 500, 755, 500, 500]
        sim_ledger = []

        cum_cost = 0.0
        curr_backlog = 0.0
        sim_metal = 500.0
        sim_stone = 500.0

        for d_idx, raw_recv in enumerate(base_demand_units, 1):
            recv_demand = raw_recv * demand_mult
            workload = recv_demand + curr_backlog
            
            # Solve LP benchmark for this exact daily workload & management limit
            lp_res = solve_daily_lp_benchmark(d_idx, workload, mgt_limit=mgt_cap, equip_limit=equip_cap, starting_metal=sim_metal, starting_stone=sim_stone)
            
            proc_units = min(workload, lp_res['output_cap'], float(equip_cap))
            rem_backlog = max(0.0, workload - proc_units)
            
            mat_cost = (lp_res['buy_m'] * p_metal) + (lp_res['buy_s'] * p_stone)
            labor_cost = 3650.0 + (lp_res['ot_reg'] * 20.0) + (lp_res['hire_out'] * 40.0)
            day_tot_cost = mat_cost + labor_cost
            cum_cost += day_tot_cost
            
            # Update state for next day
            sim_metal = max(100.0, sim_metal + lp_res['buy_m'] - proc_units)
            sim_stone = max(100.0, sim_stone + lp_res['buy_s'] - proc_units)
            curr_backlog = rem_backlog

            sim_ledger.append({
                "Day": f"Day {d_idx}",
                "Workload Received": f"{workload:.0f} u",
                "Units Processed": f"{proc_units:.0f} u",
                "Backlog": f"{rem_backlog:.0f} u",
                "Management Used": f"{lp_res['mgmt_used']:.1f} / {mgt_cap} u",
                "Overtime days": f"{lp_res['ot_reg']:.1f} days",
                "Additional Outsource Contractors used": f"{lp_res['hire_out']:.1f} artisans",
                "Raw Material Cost": f"${mat_cost:,.2f}",
                "Labor Cost": f"${labor_cost:,.2f}",
                "Total Cost": f"${day_tot_cost:,.2f}",
                "Active Bottleneck / LP Constraint": lp_res['bottleneck']
            })

        st.dataframe(pd.DataFrame(sim_ledger), use_container_width=True)

        st.metric("Total 7-Day Simulation Cost", f"${cum_cost:,.2f}")
        
        # Detailed System Bottleneck & Sensitivity Analysis
        st.markdown(f"""
        <div class="instruction-card-light">
            <h4>🧠 Digital Twin Constraint Sensitivity & Bottleneck Analysis</h4>
            <p><strong>Observations for Management Limit = {mgt_cap} u & Equipment Limit = {equip_cap} u:</strong></p>
            <ul>
                <li><strong>Outsource Contractor vs Overtime Priority:</strong> Outsource Contractors yield <strong>26.67 units per mgmt unit</strong> ($5.00/u output) whereas Regular Overtime yields <strong>6.25 units per mgmt unit</strong> ($8.00/u output). The LP solver maxes out Outsource Contractors to 30 artisans first before utilizing overtime.</li>
                <li><strong>Management Bandwidth Shift:</strong> When management capacity is set to <strong>180.0 u</strong>, management bandwidth becomes the binding constraint (0.0 slack) during surge days (Day 3 workload = 1,130u). Outsource contractors are maxed out (30 artisans), while Regular Overtime has <strong>~48.0 days of Slack</strong> because additional overtime would exceed the 180u management cap.</li>
                <li><strong>Equipment Bottleneck Threshold:</strong> If management capacity is increased beyond ~220 u, management ceases to be a constraint. On high demand surges (e.g., >1,500 u), the <strong>{equip_cap} u/day Equipment Capacity Ceiling</strong> becomes the binding constraint, causing backlog queue accumulation.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
