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
    .lp-callout-nofill {
        background-color: #ffffff !important;
        border: 2px solid #0284c7 !important;
        border-radius: 0.6rem !important;
        padding: 1.2rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    .lp-callout-nofill h3, .lp-callout-nofill h4 {
        color: #0f172a !important;
        font-weight: 800 !important;
        margin-top: 0.2rem !important;
    }
    .lp-callout-nofill p, .lp-callout-nofill span, .lp-callout-nofill div {
        color: #0f172a !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
    }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-val { font-size: 1.5rem; font-weight: 700; color: #f8fafc; }
    .score-good { color: #10b981; font-weight: bold; }
    .score-warn { color: #f59e0b; font-weight: bold; }
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
    Computes the daily LP mathematical benchmark for given demand & starting stocks.
    Returns optimal decisions: buy_m, buy_s, ot_reg, hire_out, total_cost.
    """
    try:
        prob = pulp.LpProblem(f"LP_Bench_Day_{day_idx}", pulp.LpMinimize)
        
        # Usable stock accounting for 100u safety stock floor
        usable_metal = max(0.0, starting_metal - 100.0)
        usable_stone = max(0.0, starting_stone - 100.0)
        
        # Required procurement to achieve demand
        req_proc_m = max(0.0, demand_units - usable_metal)
        req_proc_s = max(0.0, demand_units - usable_stone)
        
        # Decision variables
        buy_m = pulp.LpVariable("buy_m", lowBound=req_proc_m, cat=pulp.LpContinuous)
        buy_s = pulp.LpVariable("buy_s", lowBound=req_proc_s, cat=pulp.LpContinuous)
        ot_reg = pulp.LpVariable("ot_reg", lowBound=0.0, upBound=60.0, cat=pulp.LpContinuous)
        hire_out = pulp.LpVariable("hire_out", lowBound=0.0, upBound=30.0, cat=pulp.LpContinuous)
        
        # Output capacity constraint (regular 860u base + 0.5 OT per artisan = +2.5u per OT day)
        output_cap = 860.0 + (ot_reg * 2.5) + (hire_out * 8.0)
        prob += (output_cap >= demand_units, "Demand_Fulfillment")
        
        # Management bandwidth constraint
        prob += (164.5 + (ot_reg * 0.4) + (hire_out * 0.3) <= mgt_limit, "Management_Capacity")
        
        # Objective: Base Artisan ($3650) + OT Reg ($20/day) + Outsource ($40/day) + Raw Materials ($50/m + $100/s)
        daily_cost = 3650.0 + (ot_reg * 20.0) + (hire_out * 40.0) + (buy_m * 50.0) + (buy_s * 100.0)
        prob += daily_cost
        
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            return {
                'buy_m': float(pulp.value(buy_m)),
                'buy_s': float(pulp.value(buy_s)),
                'ot_reg': float(pulp.value(ot_reg)),
                'hire_out': float(pulp.value(hire_out)),
                'total_cost': float(pulp.value(daily_cost)),
                'status': 'Optimal'
            }
    except Exception:
        pass
        
    # Analytical Fallback
    usable_metal = max(0.0, starting_metal - 100.0)
    usable_stone = max(0.0, starting_stone - 100.0)
    buy_m_val = max(0.0, demand_units - usable_metal)
    buy_s_val = max(0.0, demand_units - usable_stone)
    
    needed_extra_units = max(0.0, demand_units - 860.0)
    if needed_extra_units <= 0:
        ot_val = 0.0
        out_val = 0.0
    else:
        ot_val = min(60.0, needed_extra_units / 2.5)
        rem_units = max(0.0, needed_extra_units - (ot_val * 2.5))
        out_val = rem_units / 8.0
        
    tot_c = 3650.0 + (ot_val * 20.0) + (out_val * 40.0) + (buy_m_val * 50.0) + (buy_s_val * 100.0)
    return {
        'buy_m': buy_m_val,
        'buy_s': buy_s_val,
        'ot_reg': ot_val,
        'hire_out': out_val,
        'total_cost': tot_c,
        'status': 'Analytical Benchmark'
    }

# --- OPTION 1: CASE STUDY TUTORIAL ---
if mode == "📖 Option 1: Case Study Introduction & Tutorial":
    st.header("📖 Case Study Introduction & Comprehensive Tutorial")
    st.info("💡 **Welcome Student!** This tutorial covers the mathematical foundations of Linear Programming (LP), Discrete Event Simulation (DES), factory process flows, resource constraints, and 2 detailed worked case examples.")
    
    tab_theory, tab_cases = st.tabs(["📘 Part 1: Theory, Setup & Constraints", "📊 Part 2: Worked Case Tutorials (Low Load vs. High Load Surge)"])
    
    with tab_theory:
        st.markdown("""
        ### 1. What is Linear Programming (LP) and Optimization?
        **Linear Programming (LP)** is a mathematical optimization technique used to achieve the best outcome (such as lowest operational cost or highest throughput) in a mathematical model whose requirements are represented by linear relationships.
        * **Objective Function:** The mathematical equation to minimize (e.g., `Total Daily Spend = Labor Costs + Material Procurement Costs`).
        * **Decision Variables:** The controllable choices available to the factory manager (Metal Purchases, Stone Purchases, Overtime Hours, Contractor Hiring).
        * **Constraints:** Real-world physical boundaries that cannot be breached (Labor Output Capacities, Equipment Capacities, Management Bandwidth, Raw Material Safety Stock Floors).

        ### 2. How Simulation & Optimization Work Together
        In real-world supply chain management, **Optimization (LP)** acts as the *Intelligent Planner*, determining the mathematically ideal decision variable values for a given single day. **Simulation (Discrete Event Simulation - DES)** acts as the *Physical Factory Engine*, moving inventory, tracking work-in-progress (WIP) queues across time, enforcing lead times, and updating order fulfillment states day-by-day.

        ### 3. Factory Process Flow & Lead Times
        The jewelry manufacturing facility operates across three sequential stages:
        1. **Design Stage (Optional):** Custom orders may optionally undergo a 1-day design phase ($100 fee), offering a 25% chance of reducing metal requirements to 0.9 units/piece (otherwise 1.0 unit).
        2. **Pre-Production Stage:** Material preparation, cutting, and shaping. Takes **1 day per unit** (Equipment capacity cap = 1,500 units/day).
        3. **Post-Production Stage:** Assembly, gem setting, and polishing (Equipment capacity cap = 1,500 units/day).
           * **Type O (Ordinary Orders):** Requires **1 day in Pre-Production + 1 day in Post-Production** (2-day manufacturing cycle).
           * **Type J (Joining Orders):** Requires **1 day in Pre-Production + 2 days in Post-Production** (3-day manufacturing cycle).

        ### 4. Resource Constraints & Operating Rules Matrix
        """)
        
        resource_df = pd.DataFrame([
            {"Artisan Class": "Regular Payroll", "Starting Staff (Pre / Post)": "60 / 70", "Daily Output Rate": "5 u/day", "Base Daily Cost": "$10/day ($2.00/u)", "Overtime Cap": "0.5 days ($20/day)", "Allowed Orders": "Type O Only", "Mgmt Cost": "0.4 u / artisan"},
            {"Artisan Class": "Skilled Payroll", "Starting Staff (Pre / Post)": "20 / 20", "Daily Output Rate": "5 u/day", "Base Daily Cost": "$15/day ($3.00/u)", "Overtime Cap": "0.5 days ($30/day)", "Allowed Orders": "Type O & Type J", "Mgmt Cost": "2.0 u / artisan"},
            {"Artisan Class": "Skilled Contractor", "Starting Staff (Pre / Post)": "10 / 15", "Daily Output Rate": "8 u/day", "Base Daily Cost": "$30/day ($3.75/u)", "Overtime Cap": "None", "Allowed Orders": "Type O & Type J", "Mgmt Cost": "1.0 u / artisan"},
            {"Artisan Class": "Outsource Contractor", "Starting Staff (Pre / Post)": "10 / 15", "Daily Output Rate": "8 u/day", "Base Daily Cost": "$40/day ($5.00/u)", "Overtime Cap": "None", "Allowed Orders": "Type O & Type J", "Mgmt Cost": "0.3 u / artisan"}
        ])
        st.table(resource_df)

        st.markdown("""
        ### 5. Raw Material Safety Floor & Procurement Math
        * **Bill of Materials (BOM):** Every finished product unit consumes **1 unit Metal ($50)** and **1 unit Stone ($100)**.
        * **Mandatory Safety Floor:** The factory must maintain a minimum of **100 units Metal** and **100 units Stone** in raw inventory at all times.
        * **Usable Stock Formula:** `Usable Stock = max(0, Current Raw Stock - 100)`
        
        > **⚠️ Procurement Math Example:**  
        > If today's incoming demand is **500 units** and starting metal raw stock is **200 units**, usable stock is only **100 units** (`200 - 100 = 100`).  
        > To fulfill the 500 units of demand, the manager **must procure at least 400 additional units** (`500 - 100 = 400`).  
        > If less than 400 units are procured, fewer units enter production, resulting in an unfulfilled **Pre-Production Backlog Queue**!
        """)

    with tab_cases:
        st.markdown("""
        ### Case Example 1: Low Order Demand Load (~500 units/day)
        When incoming daily demand is 500 units/day, the baseline regular-time staff capacity (860 units/day in Pre-Production) easily absorbs the workload during standard hours.

        #### Day-by-Day LP Decision Breakdown (Low Demand Load):
        """)
        
        low_df = pd.DataFrame([
            {"Day": "Day 1", "Workload Demand": "500 u", "Metal Procured": "100 u", "Stone Procured": "100 u", "Reg Overtime": "0.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "164.5 / 250 u", "Daily Cost": "$18,650.00", "Constraint State": "Baseline Capacity (No Overtime Needed)"},
            {"Day": "Day 2", "Workload Demand": "500 u", "Metal Procured": "500 u", "Stone Procured": "500 u", "Reg Overtime": "0.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "164.5 / 250 u", "Daily Cost": "$78,650.00", "Constraint State": "Baseline Capacity (No Overtime Needed)"},
            {"Day": "Day 3", "Workload Demand": "500 u", "Metal Procured": "500 u", "Stone Procured": "500 u", "Reg Overtime": "0.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "164.5 / 250 u", "Daily Cost": "$78,650.00", "Constraint State": "Baseline Capacity (No Overtime Needed)"},
            {"Day": "Day 4", "Workload Demand": "500 u", "Metal Procured": "500 u", "Stone Procured": "500 u", "Reg Overtime": "0.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "164.5 / 250 u", "Daily Cost": "$78,650.00", "Constraint State": "Baseline Capacity (No Overtime Needed)"},
            {"Day": "Day 5", "Workload Demand": "500 u", "Metal Procured": "500 u", "Stone Procured": "500 u", "Reg Overtime": "0.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "164.5 / 250 u", "Daily Cost": "$78,650.00", "Constraint State": "Baseline Capacity (No Overtime Needed)"},
            {"Day": "Day 6", "Workload Demand": "500 u", "Metal Procured": "500 u", "Stone Procured": "500 u", "Reg Overtime": "0.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "164.5 / 250 u", "Daily Cost": "$78,650.00", "Constraint State": "Baseline Capacity (No Overtime Needed)"},
            {"Day": "Day 7", "Workload Demand": "500 u", "Metal Procured": "500 u", "Stone Procured": "500 u", "Reg Overtime": "0.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "164.5 / 250 u", "Daily Cost": "$78,650.00", "Constraint State": "Baseline Capacity (No Overtime Needed)"}
        ])
        st.table(low_df)

        st.markdown("""
        **🎓 LP Explanation for Low Load Case:**
        * **Zero Overtime & Zero Contractor Hiring:** Baseline output (860 u/day) exceeds demand (500 u/day), so $0 is spent on overtime or contractor fees.
        * **Unbinding Management Capacity:** Management bandwidth remains at **164.5 / 250.0 units** (~65.8% utilization).
        * **Total 7-Day Spend:** **$574,550.00** with 100% On-Time Delivery fulfillment.

        ---

        ### Case Example 2: High Demand Surge Load (~1,000–1,500 units/day)
        When demand surges above 860 units/day, baseline regular-time staff is insufficient. The LP solver triggers a progressive sequence of capacity expansion measures.

        #### Day-by-Day LP Decision Breakdown (High Demand Surge Load):
        """)

        high_df = pd.DataFrame([
            {"Day": "Day 1", "Workload Demand": "500 u", "Metal Procured": "100 u", "Stone Procured": "100 u", "Reg Overtime": "0.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "164.5 / 250 u", "Daily Cost": "$18,650.00", "Constraint State": "Baseline Capacity"},
            {"Day": "Day 2", "Workload Demand": "755 u", "Metal Procured": "755 u", "Stone Procured": "755 u", "Reg Overtime": "30.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "176.5 / 250 u", "Daily Cost": "$117,500.00", "Constraint State": "🔵 Regular Payroll Overtime Active ($2.67/u output)"},
            {"Day": "Day 3", "Workload Demand": "1,130 u", "Metal Procured": "1,130 u", "Stone Procured": "1,130 u", "Reg Overtime": "60.0 days", "Outsource Hired": "15.0 artisans", "Mgmt Used": "218.1 / 250 u", "Daily Cost": "$176,100.00", "Constraint State": "🟡 Regular OT Maxed (60 days) -> Outsource Hired"},
            {"Day": "Day 4", "Workload Demand": "1,500 u", "Metal Procured": "1,500 u", "Stone Procured": "1,500 u", "Reg Overtime": "60.0 days", "Outsource Hired": "20.0 artisans", "Mgmt Used": "250.0 / 250 u", "Daily Cost": "$232,450.00", "Constraint State": "🔴 Management Bandwidth Limit (250u Cap) Maxed"},
            {"Day": "Day 5", "Workload Demand": "1,500 u", "Metal Procured": "1,500 u", "Stone Procured": "1,500 u", "Reg Overtime": "60.0 days", "Outsource Hired": "20.0 artisans", "Mgmt Used": "250.0 / 250 u", "Daily Cost": "$232,450.00", "Constraint State": "⚠️ Equipment Capacity Ceiling (1,500u Cap) Maxed"},
            {"Day": "Day 6", "Workload Demand": "1,000 u", "Metal Procured": "1,000 u", "Stone Procured": "1,000 u", "Reg Overtime": "56.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "186.9 / 250 u", "Daily Cost": "$154,770.00", "Constraint State": "🔵 Regular Payroll Overtime Active"},
            {"Day": "Day 7", "Workload Demand": "500 u", "Metal Procured": "500 u", "Stone Procured": "500 u", "Reg Overtime": "0.0 days", "Outsource Hired": "0.0 artisans", "Mgmt Used": "164.5 / 250 u", "Daily Cost": "$78,650.00", "Constraint State": "Baseline Capacity"}
        ])
        st.table(high_df)

        st.markdown("""
        **🎓 LP Explanation for High Demand Surge Case:**
        1. **Level 1 Bottleneck (Regular Payroll Overtime @ Day 2):** At 755u demand, the LP activates **30.0 days of Regular Payroll overtime**. Because Regular Payroll overtime costs **$2.67/unit output**, it is the cheapest way to expand capacity.
        2. **Level 2 Bottleneck (Outsource Contractor Hiring @ Day 3):** At 1,130u demand, Regular Payroll overtime maxes out at **60.0 days (+150u output)**. The LP is forced to recruit **15 Outsource Contractors** ($5.00/u output) to cover the remaining volume.
        3. **Level 3 Bottleneck (Management Capacity Cap @ Day 4):** At 1,500u demand, management utilization hits the absolute **250.0 / 250.0 units cap**, preventing further labor expansion.
        4. **Level 4 Bottleneck (Equipment Capacity Ceiling @ Day 5):** Physical machine throughput caps at **1,500 units/day**, causing unprocessed orders to form a **Pre-Production Backlog Queue**.
        """)

# --- OPTION 2: MODE 1 DAILY DECISION GAME ---
elif mode == "🎮 Option 2: Mode 1 - Daily Decision Game":
    st.header("🎮 Mode 1: Interactive Daily Decision Game (Player vs LP Benchmark)")
    
    # Quick Reference Expander
    with st.expander("📌 Quick Reference: Factory Setup, Process Flow & Resource Constraints", expanded=False):
        st.markdown("""
        * **Manufacturing Lead Times:** Type O = 2 days (1 Pre + 1 Post), Type J = 3 days (1 Pre + 2 Post).
        * **Process Constraints:** Pre-Prod Cap = 1,500 u/day, Post-Prod Cap = 1,500 u/day.
        * **Raw Material Safety Floor:** Minimum 100 units Metal & 100 units Stone must be preserved at all times (`Usable Stock = Current Stock - 100`).
        * **Management Budget Cap:** 250.0 units/day max management bandwidth.
        * **Labor Costs:** Regular Payroll Overtime = $20/day ($2.67/u output), Outsource Contractors = $40/day ($5.00/u output).
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
        st.session_state.submitted_day_results = None

    if st.session_state.day <= 7:
        st.subheader(f"📅 Simulation State: Day {st.session_state.day} of 7")

        # Student Instructions Card (White Background, Dark Navy Text)
        st.markdown(f"""
        <div class="instruction-card-light">
            <h3>✍️ Student Instructions for Day {st.session_state.day}: Select Your 4 Decision Variables</h3>
            <p>Welcome Factory Manager! Review today's incoming demand and backlog below. Select values for the <strong>4 Decision Variables</strong>, then click <strong>📩 Submit Decisions for Day {st.session_state.day}</strong> to evaluate your performance against the Linear Program (LP) benchmark.</p>
            <ul>
                <li><strong>1. Metal Purchase (units):</strong> Procure metal @ $50/unit (Remember to maintain the mandatory 100-unit safety floor!).</li>
                <li><strong>2. Stone Purchase (units):</strong> Procure stone @ $100/unit (Remember to maintain the mandatory 100-unit safety floor!).</li>
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

        st.info(f"📦 **Today's Incoming Demand (Day {st.session_state.day}):** {curr_demand['count']} Orders ({curr_demand['units']} units) — *{curr_demand['desc']}* | **Total Workload Queue to Process:** {tot_queue_today:.0f} units")

        # STAGE 1: DECISION FORM
        if st.session_state.submitted_day_results is None:
            with st.form("daily_decision_form"):
                st.write(f"### 🛠️ Step 1: Select Decision Variables for Day {st.session_state.day}")
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

                submit_btn = st.form_submit_button(f"📩 Submit Decisions for Day {st.session_state.day}", type="primary")

            if submit_btn:
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
                
                st.session_state.submitted_day_results = {
                    'day': st.session_state.day,
                    'is_feasible': is_feasible,
                    'player_m': buy_m, 'lp_m': lp_res['buy_m'],
                    'player_s': buy_s, 'lp_s': lp_res['buy_s'],
                    'player_ot': ot_reg, 'lp_ot': lp_res['ot_reg'],
                    'player_out': hire_out, 'lp_out': lp_res['hire_out'],
                    'player_cost': player_day_cost, 'lp_cost': lp_day_cost,
                    'efficiency': efficiency,
                    'score_str': score_str,
                    'feasible_prod': feasible_prod,
                    'unprocessed': unprocessed,
                    'buy_m': buy_m, 'buy_s': buy_s
                }
                st.rerun()

        # STAGE 2: DISPLAY LP SOLUTION & COMPARISON
        else:
            comp = st.session_state.submitted_day_results
            st.markdown("---")
            st.write(f"### 📊 Step 2: Day {comp['day']} Decision Analysis & LP Solution Comparison")
            
            if not comp['is_feasible']:
                st.error("🚨 PRODUCTION STALLED / FEASIBILITY FAILURE: Your material purchases or labor capacity were insufficient to process the workload, or raw material fell below the 100u safety floor. Production stalled and a 0.0% score was assigned for the turn.")
            
            # Side-by-side comparison table
            comp_df = pd.DataFrame([
                {"Decision Variable": "1. Metal Purchase (units)", "Player Choice": f"{comp['player_m']:.0f} u", "LP Optimal Choice": f"{comp['lp_m']:.0f} u", "Cost Impact": f"${((comp['player_m'] - comp['lp_m']) * 50):,.2f}"},
                {"Decision Variable": "2. Stone Purchase (units)", "Player Choice": f"{comp['player_s']:.0f} u", "LP Optimal Choice": f"{comp['lp_s']:.0f} u", "Cost Impact": f"${((comp['player_s'] - comp['lp_s']) * 100):,.2f}"},
                {"Decision Variable": "3. Regular Payroll Overtime (days)", "Player Choice": f"{comp['player_ot']:.1f} days", "LP Optimal Choice": f"{comp['lp_ot']:.1f} days", "Cost Impact": f"${((comp['player_ot'] - comp['lp_ot']) * 20):,.2f}"},
                {"Decision Variable": "4. Outsource Contractors Hired (artisans)", "Player Choice": f"{comp['player_out']:.1f} artisans", "LP Optimal Choice": f"{comp['lp_out']:.1f} artisans", "Cost Impact": f"${((comp['player_out'] - comp['lp_out']) * 40):,.2f}"},
                {"Decision Variable": "TOTAL DAILY OPERATIONAL SPEND", "Player Choice": f"${comp['player_cost']:,.2f}", "LP Optimal Choice": f"${comp['lp_cost']:,.2f}", "Cost Impact": f"${(comp['player_cost'] - comp['lp_cost']):,.2f}"}
            ])
            st.table(comp_df)

            diff_cost = comp['player_cost'] - comp['lp_cost']
            if diff_cost > 1.0:
                st.warning(f"""
                #### 🔵 Comparative Situation Analysis: Player Spend is Higher (+${diff_cost:,.2f})
                **Why the LP Solution Choice is Better & More Optimal:**
                1. **Material Procurement Efficiency:** The LP purchased the exact minimum raw materials needed to preserve the 100u safety floor without locking up excess cash in inventory.
                2. **Labor Class Cost Hierarchy:** Regular Payroll Overtime ($20/day = $2.67/unit output) is far cheaper than Outsource Contractors ($40/day = $5.00/unit output). The LP maxed out cheap overtime before hiring contractors.
                3. **Management Bandwidth Protection:** The LP carefully balances overtime and contractor hiring to stay within the 250u management cap.
                """)
            elif diff_cost < -1.0:
                st.info(f"""
                #### 🟠 Comparative Situation Analysis: Player Spend is Lower (${diff_cost:,.2f} less)
                **Why the LP Solution Choices are Necessary & Optimal:**
                1. **Preventing Production Stalls:** While your daily cash outflow appeared lower, under-purchasing materials risks stalling production or violating the 100u safety floor.
                2. **Preventing Backlog Accumulation:** Under-investing in labor causes orders to get trapped in the backlog queue, risking late delivery penalties.
                3. **Full Demand Fulfillment:** The LP spend is optimal because it guarantees 100% throughput while maintaining the 100u safety floor.
                """)
            else:
                st.success("🌟 **PERFECT OPTIMIZATION MATCH!** Your decision choices matched the LP optimal benchmark perfectly across all 4 variables.")

            # White Fill Callout Banner directing to Next Step
            st.markdown("""
            <div class="lp-callout-nofill">
                <h4>👉 LP Solution Analysis Complete!</h4>
                <p>Review the LP optimal choices and comparative analysis above. When you are ready to advance the factory to the next simulation day, click the button below.</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"▶ Step 1 Day Forward to Day {st.session_state.day + 1}", type="primary"):
                # Execute day state update
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
                st.session_state.submitted_day_results = None
                st.rerun()

        if st.session_state.game_history:
            st.write("### 📈 7-Day Performance Ledger")
            st.dataframe(pd.DataFrame(st.session_state.game_history), width='stretch')

    else:
        st.balloons()
        st.success("🎉 **7-DAY SIMULATION COMPLETED!** All 7 days have been processed. Review your final performance summary below.")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Player Spend", f"${st.session_state.cum_player_cost:,.2f}")
        c2.metric("Total LP Optimal Benchmark", f"${st.session_state.cum_lp_cost:,.2f}")
        gap = st.session_state.cum_player_cost - st.session_state.cum_lp_cost
        c3.metric("Total Cost Gap", f"${gap:,.2f}", delta="-Excess Spend" if gap > 0 else "+Optimal")

        st.write("### 📈 Final 7-Day Performance Ledger")
        st.dataframe(pd.DataFrame(st.session_state.game_history), width='stretch')

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
            st.session_state.submitted_day_results = None
            st.rerun()

# --- OPTION 3: MODE 2 DIGITAL TWIN SANDBOX ---
else:
    st.header("🔬 Mode 2: Digital Twin Sensitivity Sandbox")
    st.info("💡 **Goal:** Test how changing factory constraints, demand multipliers, and order mix alters 7-day costs and throughput. Observe how system bottlenecks shift dynamically day-by-day!")

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
        st.write("### 📈 7-Day Digital Twin Simulation Results Ledger")
        
        base_demand_units = [500, 755, 1130, 500, 755, 500, 500]
        sim_data = []

        cum_cost = 0.0
        backlog = 0.0
        starting_m = 500.0
        starting_s = 500.0

        for d_idx, base_u in enumerate(base_demand_units, 1):
            raw_req = int(base_u * demand_mult)
            workload_recv = raw_req + backlog
            
            # Usable materials
            usable_m = max(0.0, starting_m - 100.0)
            usable_s = max(0.0, starting_s - 100.0)
            proc_m = max(0.0, workload_recv - usable_m)
            proc_s = max(0.0, workload_recv - usable_s)
            
            mat_cost = (proc_m * p_metal) + (proc_s * p_stone)
            
            # Labor output capacity calculation
            # Regular output = 860u. Extra needed = workload_recv - 860u
            extra_needed = max(0.0, workload_recv - 860.0)
            
            # Max regular OT = 60 days (+150u)
            ot_days = min(60.0, extra_needed / 2.5)
            rem_needed = max(0.0, extra_needed - (ot_days * 2.5))
            
            # Outsource contractors needed (+8u per artisan)
            out_artisans = rem_needed / 8.0
            
            mgt_used = 164.5 + (ot_days * 0.4) + (out_artisans * 0.3)
            
            # Bottleneck identification
            if mgt_used > mgt_cap:
                mgt_used = mgt_cap
                bottleneck = "🔴 Management Bandwidth Limit Maxed"
            elif workload_recv > equip_cap:
                bottleneck = "⚠️ Equipment Capacity Ceiling Reached"
            elif ot_days >= 60.0:
                bottleneck = "🟡 Regular Overtime Limit Reached (60 days max)"
            elif ot_days > 0.0:
                bottleneck = "🔵 Regular Payroll Overtime Active"
            else:
                bottleneck = "🟢 Baseline Capacity (No Bottleneck)"
                
            labor_cost = 3650.0 + (ot_days * 20.0) + (out_artisans * 40.0)
            tot_cost = mat_cost + labor_cost
            cum_cost += tot_cost
            
            units_proc = min(workload_recv, equip_cap, 860.0 + ot_days*2.5 + out_artisans*8.0)
            backlog = max(0.0, workload_recv - units_proc)

            sim_data.append({
                "Day": f"Day {d_idx}",
                "Workload Received": f"{workload_recv:.0f} u",
                "Units Processed": f"{units_proc:.0f} u",
                "Backlog": f"{backlog:.0f} u",
                "Management Used": f"{mgt_used:.1f} / {mgt_cap:.1f} u",
                "Overtime days": f"{ot_days:.1f} days",
                "Additional Outsource Contractors used": f"{out_artisans:.1f} artisans",
                "Raw Material Cost": f"${mat_cost:,.2f}",
                "Labor Cost": f"${labor_cost:,.2f}",
                "Total Cost": f"${tot_cost:,.2f}",
                "Active Bottleneck / LP Constraint": bottleneck
            })

            starting_m = max(100.0, starting_m + proc_m - units_proc)
            starting_s = max(100.0, starting_s + proc_s - units_proc)

        st.dataframe(pd.DataFrame(sim_data), width='stretch')

        st.metric("Total 7-Day Simulation Operational Spend", f"${cum_cost:,.2f}")
        
        # Sensitivity Analysis Writeup
        st.markdown("---")
        st.write("### 🧠 Parameter Sensitivity & Bottleneck Shift Analysis")
        st.info(f"""
        **System Sensitivity Insights for Current Settings:**
        1. **Management Capacity Sensitivity (Current Limit = {mgt_cap} u):** If management capacity is increased beyond ~220 units/day, management ceases to be a binding constraint. The primary bottleneck shifts entirely to the **{equip_cap} units/day Equipment Capacity Ceiling**.
        2. **Demand Multiplier Impact (Current Multiplier = {demand_mult}x):** At demand multipliers > 1.5x, Regular Payroll overtime reaches its 60-day cap (+150u output). The solver is forced to recruit Outsource Contractors ($5.00/u output), inflating daily labor costs by +87.5%.
        3. **Type J Order Mix Dwell Time Impact (Current Ratio = {type_j_ratio}%):** Type J orders require 2 days in Post-Production finishing. Increasing the Type J ratio above 30% increases Post-Production WIP dwell time, reducing weekly order completions and increasing work-in-progress holding costs.
        """)
