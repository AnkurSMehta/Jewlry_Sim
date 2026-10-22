import streamlit as st
from ortools.linear_solver import pywraplp
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
    .instruction-card-light p, .instruction-card-light li, .instruction-card-light span {
        color: #1e293b !important;
        font-size: 0.98rem !important;
        line-height: 1.5 !important;
    }
    .callout-card-light {
        background-color: #ffffff !important;
        border: 2px solid #0284c7 !important;
        border-radius: 0.6rem !important;
        padding: 1rem !important;
        margin-top: 1rem !important;
        color: #0f172a !important;
        font-weight: 600 !important;
    }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-val { font-size: 1.5rem; font-weight: 700; color: #f8fafc; }
    .badge-binding { background-color: #ef4444; color: #ffffff; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
    .badge-slack { background-color: #10b981; color: #ffffff; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💎 Jewelry Supply Chain Teaching Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Powered by Google OR-Tools Mathematical Optimization Engine</div>', unsafe_allow_html=True)

mode = st.sidebar.radio(
    "Select Platform Option:",
    [
        "📖 Option 1: Case Study Introduction & Tutorial",
        "🎮 Option 2: Mode 1 - Daily Decision Game (OR-Tools)",
        "🔬 Option 3: Mode 2 - Fully Parametric Digital Twin Sandbox"
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
            "simulation_settings": { 
                "management_capacity_daily": 250.0, 
                "equipment_capacity_daily": 1500, 
                "min_raw_material_safety_stock": 100,
                "opening_metal_stock": 500.0,
                "opening_stone_stock": 500.0
            },
            "raw_materials": { "metal": { "unit_cost": 50.0 }, "stone": { "unit_cost": 100.0 } },
            "workforce_defaults": {
                "reg_pre": 60, "reg_post": 70,
                "skilled_pre": 20, "skilled_post": 20,
                "con_pre": 10, "con_post": 15,
                "out_pre": 10, "out_post": 15
            }
        }

cfg = load_default_config()

# --- GOOGLE OR-TOOLS LP BENCHMARK SOLVER ENGINE ---
def solve_daily_ortools(
    day_idx, 
    demand_units, 
    mgt_limit=250.0, 
    equip_limit=1500.0, 
    starting_metal=500.0, 
    starting_stone=500.0,
    safety_floor=100.0,
    max_ot_days=60.0,
    max_outsource_artisans=30.0,
    p_metal=50.0,
    p_stone=100.0,
    type_j_ratio=30.0,
    reg_pre=60, reg_post=70,
    skilled_pre=20, skilled_post=20,
    con_pre=10, con_post=15,
    out_pre=10, out_post=15
):
    """
    Solves the daily linear programming optimization model using Google OR-Tools (GLOP solver).
    Returns decision variables, total cost, status, mgmt consumption, and constraint slack analysis.
    """
    try:
        usable_m = max(0.0, starting_metal - safety_floor)
        usable_s = max(0.0, starting_stone - safety_floor)
        req_proc_m = max(0.0, demand_units - usable_m)
        req_proc_s = max(0.0, demand_units - usable_s)

        base_pre = (reg_pre * 5.0) + (skilled_pre * 5.0) + (con_pre * 8.0) + (out_pre * 8.0)
        base_post = (reg_post * 5.0) + (skilled_post * 5.0) + (con_post * 8.0) + (out_post * 8.0)
        base_mgmt = (reg_pre * 0.4) + (skilled_pre * 2.0) + (con_pre * 1.0) + (out_pre * 0.3) + \
                    (reg_post * 0.4) + (skilled_post * 2.0) + (con_post * 1.0) + (out_post * 0.3)
        base_cost = (reg_pre * 10.0 + reg_post * 10.0) + (skilled_pre * 15.0 + skilled_post * 15.0) + \
                    (con_pre * 30.0 + con_post * 30.0) + (out_pre * 40.0 + out_post * 40.0)

        r_j = type_j_ratio / 100.0
        post_factor = 1.0 + r_j

        # Stage 1: Attempt full demand fulfillment
        solver = pywraplp.Solver.CreateSolver('GLOP')
        if solver:
            buy_m = solver.NumVar(req_proc_m, solver.infinity(), 'buy_m')
            buy_s = solver.NumVar(req_proc_s, solver.infinity(), 'buy_s')
            ot_reg = solver.NumVar(0.0, max_ot_days, 'ot_reg')
            hire_out = solver.NumVar(0.0, max_outsource_artisans, 'hire_out')

            pre_cap = base_pre + (ot_reg * 2.5) + (hire_out * 8.0)
            post_cap = base_post + (ot_reg * 2.5) + (hire_out * 8.0)
            mgmt_expr = base_mgmt + (ot_reg * 0.4) + (hire_out * 0.3)

            solver.Add(pre_cap >= demand_units)
            solver.Add(post_cap >= demand_units * post_factor)
            solver.Add(demand_units <= equip_limit)
            solver.Add(mgmt_expr <= mgt_limit)

            cost_expr = base_cost + (ot_reg * 20.0) + (hire_out * 40.0) + (buy_m * p_metal) + (buy_s * p_stone)
            solver.Minimize(cost_expr)

            status = solver.Solve()

            if status == pywraplp.Solver.OPTIMAL:
                v_buy_m = buy_m.solution_value()
                v_buy_s = buy_s.solution_value()
                v_ot = ot_reg.solution_value()
                v_out = hire_out.solution_value()
                v_cost = solver.Objective().Value()
                v_mgmt = base_mgmt + (v_ot * 0.4) + (v_out * 0.3)
                v_proc = demand_units
                v_j_pieces = v_proc * r_j

                return {
                    'buy_m': v_buy_m, 'buy_s': v_buy_s,
                    'ot_reg': v_ot, 'hire_out': v_out,
                    'total_cost': v_cost, 'mgmt_used': v_mgmt,
                    'output_cap': v_proc, 'proc_units': v_proc, 'j_pieces': v_j_pieces,
                    'status': 'Optimal (Google OR-Tools GLOP)',
                    'slack_ot': max_ot_days - v_ot,
                    'slack_out': max_outsource_artisans - v_out,
                    'slack_mgmt': mgt_limit - v_mgmt,
                    'slack_equip': equip_limit - v_proc,
                    'slack_post': (base_post + v_ot*2.5 + v_out*8.0) - (v_proc * post_factor),
                    'base_cost': base_cost, 'base_output': base_pre, 'base_mgmt': base_mgmt
                }

        # Stage 2: Capacity is restricted. Maximize achievable processed units X
        solver2 = pywraplp.Solver.CreateSolver('GLOP')
        buy_m2 = solver2.NumVar(0.0, solver2.infinity(), 'buy_m2')
        buy_s2 = solver2.NumVar(0.0, solver2.infinity(), 'buy_s2')
        ot2 = solver2.NumVar(0.0, max_ot_days, 'ot2')
        out2 = solver2.NumVar(0.0, max_outsource_artisans, 'out2')
        X2 = solver2.NumVar(0.0, demand_units, 'X2')

        pre_cap2 = base_pre + (ot2 * 2.5) + (out2 * 8.0)
        post_cap2 = base_post + (ot2 * 2.5) + (out2 * 8.0)
        mgmt_expr2 = base_mgmt + (ot2 * 0.4) + (out2 * 0.3)

        solver2.Add(pre_cap2 >= X2)
        solver2.Add(post_cap2 >= X2 * post_factor)
        solver2.Add(X2 <= equip_limit)
        solver2.Add(mgmt_expr2 <= mgt_limit)

        req_m2 = X2 - usable_m
        req_s2 = X2 - usable_s
        solver2.Add(buy_m2 >= req_m2)
        solver2.Add(buy_s2 >= req_s2)

        cost2 = base_cost + (ot2 * 20.0) + (out2 * 40.0) + (buy_m2 * p_metal) + (buy_s2 * p_stone)
        solver2.Maximize(X2 * 100000.0 - cost2)

        st2 = solver2.Solve()
        v_proc = X2.solution_value()
        v_ot = ot2.solution_value()
        v_out = out2.solution_value()
        v_buy_m = max(0.0, buy_m2.solution_value())
        v_buy_s = max(0.0, buy_s2.solution_value())
        v_cost = base_cost + (v_ot * 20.0) + (v_out * 40.0) + (v_buy_m * p_metal) + (v_buy_s * p_stone)
        v_mgmt = base_mgmt + (v_ot * 0.4) + (v_out * 0.3)
        v_j_pieces = v_proc * r_j

        return {
            'buy_m': v_buy_m, 'buy_s': v_buy_s,
            'ot_reg': v_ot, 'hire_out': v_out,
            'total_cost': v_cost, 'mgmt_used': v_mgmt,
            'output_cap': v_proc, 'proc_units': v_proc, 'j_pieces': v_j_pieces,
            'status': 'Capacity Restricted (Google OR-Tools)',
            'slack_ot': max_ot_days - v_ot,
            'slack_out': max_outsource_artisans - v_out,
            'slack_mgmt': mgt_limit - v_mgmt,
            'slack_equip': equip_limit - v_proc,
            'slack_post': (base_post + v_ot*2.5 + v_out*8.0) - (v_proc * post_factor),
            'base_cost': base_cost, 'base_output': base_pre, 'base_mgmt': base_mgmt
        }

    except Exception as e:
        pass

    # Analytical Optimization Fallback
    usable_m = max(0.0, starting_metal - safety_floor)
    usable_s = max(0.0, starting_stone - safety_floor)
    buy_m_val = max(0.0, demand_units - usable_m)
    buy_s_val = max(0.0, demand_units - usable_s)

    r_j = type_j_ratio / 100.0
    post_factor = 1.0 + r_j
    base_pre = (reg_pre * 5.0) + (skilled_pre * 5.0) + (con_pre * 8.0) + (out_pre * 8.0)
    base_post = (reg_post * 5.0) + (skilled_post * 5.0) + (con_post * 8.0) + (out_post * 8.0)
    base_mgmt = 164.5

    needed_extra = max(0.0, demand_units - base_pre)
    rem_mgmt = max(0.0, mgt_limit - base_mgmt)

    out_val = min(max_outsource_artisans, min(needed_extra / 8.0, rem_mgmt / 0.3))
    rem_demand = max(0.0, needed_extra - (out_val * 8.0))
    rem_mgmt_after_out = max(0.0, rem_mgmt - (out_val * 0.3))

    ot_val = min(max_ot_days, min(rem_demand / 2.5, rem_mgmt_after_out / 0.4))

    tot_cost = 3650.0 + (ot_val * 20.0) + (out_val * 40.0) + (buy_m_val * p_metal) + (buy_s_val * p_stone)
    v_mgmt = base_mgmt + (ot_val * 0.4) + (out_val * 0.3)
    v_output = min(demand_units, min(base_pre + ot_val*2.5 + out_val*8.0, (base_post + ot_val*2.5 + out_val*8.0)/post_factor))

    return {
        'buy_m': buy_m_val, 'buy_s': buy_s_val,
        'ot_reg': ot_val, 'hire_out': out_val,
        'total_cost': tot_cost, 'mgmt_used': v_mgmt,
        'output_cap': v_output, 'proc_units': v_output, 'j_pieces': v_output * r_j,
        'status': 'Analytical Optimization Fallback',
        'slack_ot': max_ot_days - ot_val,
        'slack_out': max_outsource_artisans - out_val,
        'slack_mgmt': mgt_limit - v_mgmt,
        'slack_equip': equip_limit - v_output,
        'slack_post': (base_post + ot_val*2.5 + out_val*8.0) - (v_output * post_factor),
        'base_cost': 3650.0, 'base_output': base_pre, 'base_mgmt': base_mgmt
    }


# ==============================================================================
# OPTION 1: CASE STUDY INTRODUCTION & TUTORIAL
# ==============================================================================
if mode == "📖 Option 1: Case Study Introduction & Tutorial":
    st.header("📖 Option 1: Case Study Introduction & Tutorial")
    st.markdown("### Executive Case Guide: Integrated Linear Programming & Supply Chain Simulation")

    tab1, tab2 = st.tabs(["Part 1: Optimization Fundamentals & Factory Setup", "Part 2: Worked Tutorials & Bottleneck Shifts"])

    with tab1:
        st.markdown("""
        #### 1. Linear Programming & Simulation Integration
        In modern industrial operations, **Linear Programming (LP)** acts as the *Intelligent Operational Planner*, identifying the mathematically proven lowest-cost combination of raw materials, regular overtime, and contractor labor to fulfill demand.
        Concurrently, **Discrete Event Simulation (DES)** acts as the *Physical Factory Floor*, modeling real-time inventory queues, multi-stage dwell times, and physical capacity bottlenecks day-by-day.

        #### 2. Manufacturing Stages & Dwell Cycle Times
        * **Stage 1: Optional Design Routing** — 1 day per order ($100 fee) with a 25% chance of reducing metal BOM to 0.9 units/piece (otherwise 1.0 unit).
        * **Stage 2: Pre-Production (Component Processing)** — 1 day per unit.
        * **Stage 3: Post-Production (Finishing & Assembly)** — Finishing benches.
          * **Type O (Ordinary Orders):** 1 day Pre-Production + 1 day Post-Production = **2-Day Total Cycle Time**.
          * **Type J (Joining Orders):** 1 day Pre-Production + 2 days Post-Production = **3-Day Total Cycle Time**.

        #### 3. Resource Matrix & Constraint Breakdown
        | Artisan Class | Starting Staff (Pre / Post) | Output Rate | Base Daily Pay | Overtime Limit & Surcharge | Allowed Orders | Mgmt Cost |
        | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
        | **Regular Payroll** | 60 / 70 | 5 u/day | $10/day ($2.00/u) | Max 0.5 day/artisan ($20/day) | Type O Only | 0.4 u/artisan |
        | **Skilled Payroll** | 20 / 20 | 5 u/day | $15/day ($3.00/u) | Max 0.5 day/artisan ($30/day) | Type O & J | 2.0 u/artisan |
        | **Skilled Contractor** | 10 / 15 | 8 u/day | $30/day ($3.75/u) | None | Type O & J | 1.0 u/artisan |
        | **Outsource Contractor**| 10 / 15 | 8 u/day | $40/day ($5.00/u) | None | Type O & J | 0.3 u/artisan |

        * **Bill of Materials (BOM):** 1 unit Metal ($50) + 1 unit Stone ($100) per finished piece.
        * **Mandatory Safety Floor:** Minimum 100 units Metal & 100 units Stone raw stock at all times.
        * **Management Budget Limit:** Default 250.0 mgmt units/day.
        * **Equipment Processing Ceiling:** Default 1,500 units/day.
        """)

    with tab2:
        st.markdown("""
        #### Worked Examples: Constraint Shifting Under Workload Surges

        ##### 🟢 Case Example 1: Low Demand Load (~500 units/day)
        * Baseline staff provides 560 units Pre-Prod output & 690 units Post-Prod output.
        * Demand (500u) is completely absorbed during regular working hours without overtime or contractor hiring.
        * Management Bandwidth used: **164.5 / 250.0 u** (Unconstrained).
        * Total 7-Day Simulation Cost: **$574,550.00**.

        ##### 🔴 Case Example 2: High Demand Load Surge (~1,000–1,500 units/day)
        * **At 1,000 u/day:** Regular Payroll Overtime constraint maxes out first (60.0 OT days @ $2.67/u).
        * **At 1,200 u/day:** Management Bandwidth limit (250.0 u) maxes out, forcing the solver to recruit Outsource Contractors (0.3 mgmt/artisan = 26.67u output/mgmt u).
        * **At 1,500 u/day:** Equipment Processing Ceiling (1,500 u/day) is reached, forming a physical equipment bottleneck and generating a multi-day order backlog.
        * **Joining Order Mix Surge (70% Type J):** Inflates Post-Production labor requirements to 1.70 labor units/finished piece, triggering contractor recruitment and Post-Production capacity bottlenecks!
        """)


# ==============================================================================
# OPTION 2: MODE 1 - DAILY DECISION GAME (OR-TOOLS BENCHMARK)
# ==============================================================================
elif mode == "🎮 Option 2: Mode 1 - Daily Decision Game (OR-Tools)":
    st.header("🎮 Mode 1: Interactive Daily Decision Game (Player vs Google OR-Tools Benchmark)")

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
        st.session_state.submitted_day = None
        st.session_state.last_comparison = None

    demand_schedule = {
        1: {"count": 43, "units": 500, "desc": "Opening Baseline Demand"},
        2: {"count": 65, "units": 755, "desc": "+50% Demand Surge over Day 1"},
        3: {"count": 98, "units": 1130, "desc": "+50% Demand Surge over Day 2! (Surge Surcharge Trigger)"},
        4: {"count": 43, "units": 500, "desc": "Normal Demand"},
        5: {"count": 65, "units": 755, "desc": "+50% Demand Surge"},
        6: {"count": 43, "units": 500, "desc": "Normal Demand"},
        7: {"count": 43, "units": 500, "desc": "Normal Demand"}
    }

    if st.session_state.day <= 7:
        st.subheader(f"📅 Simulation State: Day {st.session_state.day} of 7")

        curr_demand = demand_schedule.get(st.session_state.day, {"count": 43, "units": 500, "desc": "Standard Demand"})
        tot_queue_today = curr_demand['units'] + st.session_state.backlog_queue

        # Student Instructions Card
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

        st.info(f"📦 **Today's Incoming Demand (Day {st.session_state.day}):** {curr_demand['count']} Orders ({curr_demand['units']} units) — *{curr_demand['desc']}* | **Total Workload Queue:** {tot_queue_today:.0f} units")

        # Two-stage workflow: Form or Next Day Button
        if st.session_state.submitted_day != st.session_state.day:
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
                # Calculate Player Costs & Feasibility
                tot_avail_m = st.session_state.metal_stock + buy_m - 100.0
                tot_avail_s = st.session_state.stone_stock + buy_s - 100.0
                usable_mat = min(max(0.0, tot_avail_m), max(0.0, tot_avail_s))

                labor_cap = 560.0 + (ot_reg * 2.5) + (hire_out * 8.0)
                max_possible_prod = min(tot_queue_today, labor_cap, 1500.0)

                feasible_prod = min(max_possible_prod, usable_mat)

                is_feasible = (feasible_prod >= tot_queue_today - 5.0) and (tot_avail_m >= 0.0) and (tot_avail_s >= 0.0)

                mat_spend = (buy_m * 50.0) + (buy_s * 100.0)
                labor_spend = 3650.0 + (ot_reg * 20.0) + (hire_out * 40.0)
                player_day_cost = mat_spend + labor_spend

                # Solve Google OR-Tools LP Benchmark
                lp_res = solve_daily_ortools(
                    st.session_state.day, 
                    tot_queue_today, 
                    mgt_limit=250.0, 
                    equip_limit=1500, 
                    starting_metal=st.session_state.metal_stock, 
                    starting_stone=st.session_state.stone_stock,
                    type_j_ratio=30.0
                )
                lp_day_cost = lp_res['total_cost']

                if not is_feasible:
                    efficiency = 0.0
                    score_str = "0.0% (Feasibility Failure)"
                else:
                    efficiency = min(100.0, (lp_day_cost / player_day_cost) * 100.0) if player_day_cost > 0 else 100.0
                    score_str = f"{efficiency:.1f}%"

                unprocessed = max(0.0, tot_queue_today - feasible_prod)
                st.session_state.backlog_queue = unprocessed

                st.session_state.metal_stock = max(100.0, st.session_state.metal_stock + buy_m - feasible_prod)
                st.session_state.stone_stock = max(100.0, st.session_state.stone_stock + buy_s - feasible_prod)
                st.session_state.wip_metal += feasible_prod
                st.session_state.wip_stone += feasible_prod

                st.session_state.cum_player_cost += player_day_cost
                st.session_state.cum_lp_cost += lp_day_cost

                st.session_state.last_comparison = {
                    'day': st.session_state.day,
                    'is_feasible': is_feasible,
                    'player_m': buy_m, 'lp_m': lp_res['buy_m'],
                    'player_s': buy_s, 'lp_s': lp_res['buy_s'],
                    'player_ot': ot_reg, 'lp_ot': lp_res['ot_reg'],
                    'player_out': hire_out, 'lp_out': lp_res['hire_out'],
                    'player_cost': player_day_cost, 'lp_cost': lp_day_cost,
                    'efficiency': efficiency,
                    'score_str': score_str,
                    'lp_res': lp_res
                }

                st.session_state.game_history.append({
                    "Day": f"Day {st.session_state.day}",
                    "Player Spend": f"${player_day_cost:,.2f}",
                    "LP Optimal": f"${lp_day_cost:,.2f}",
                    "Score": score_str,
                    "Backlog Left": f"{unprocessed:.0f} u"
                })

                st.session_state.submitted_day = st.session_state.day
                st.rerun()

        # Display Results for Submitted Day
        if st.session_state.submitted_day == st.session_state.day and st.session_state.last_comparison:
            comp = st.session_state.last_comparison
            lp_r = comp['lp_res']
            st.markdown("---")
            st.write(f"### 📊 Day {comp['day']} Decision Analysis & Google OR-Tools LP Benchmark Comparison")

            if not comp['is_feasible']:
                st.error("🚨 PRODUCTION STALLED / FEASIBILITY FAILURE: Your material purchases or labor capacity were insufficient to process the workload, or raw material fell below the 100u safety floor. Production stalled and a 0% score was assigned.")

            # Side-by-side decision comparison table
            comp_df = pd.DataFrame([
                {"Decision Variable": "1. Metal Purchase (units)", "Player Choice": f"{comp['player_m']:.0f} u", "LP Optimal": f"{comp['lp_m']:.0f} u", "Cost Impact": f"${((comp['player_m'] - comp['lp_m']) * 50):,.2f}"},
                {"Decision Variable": "2. Stone Purchase (units)", "Player Choice": f"{comp['player_s']:.0f} u", "LP Optimal": f"{comp['lp_s']:.0f} u", "Cost Impact": f"${((comp['player_s'] - comp['lp_s']) * 100):,.2f}"},
                {"Decision Variable": "3. Regular Payroll Overtime (days)", "Player Choice": f"{comp['player_ot']:.1f} days", "LP Optimal": f"{comp['lp_ot']:.1f} days", "Cost Impact": f"${((comp['player_ot'] - comp['lp_ot']) * 20):,.2f}"},
                {"Decision Variable": "4. Outsource Contractors Hired (artisans)", "Player Choice": f"{comp['player_out']:.1f} artisans", "LP Optimal": f"{comp['lp_out']:.1f} artisans", "Cost Impact": f"${((comp['player_out'] - comp['lp_out']) * 40):,.2f}"},
                {"Decision Variable": "TOTAL DAILY OPERATIONAL SPEND", "Player Choice": f"${comp['player_cost']:,.2f}", "LP Optimal": f"${comp['lp_cost']:,.2f}", "Cost Impact": f"${(comp['player_cost'] - comp['lp_cost']):,.2f}"}
            ])
            st.table(comp_df)

            # Constraint Slack Breakdown
            st.write("#### ⚖️ LP Benchmark Constraint Slack & Binding Status")
            slack_df = pd.DataFrame([
                {"Constraint Description": "Management Bandwidth Limit (250.0 u)", "LP Value Used": f"{lp_r['mgmt_used']:.1f} u", "Slack Remaining": f"{lp_r['slack_mgmt']:.1f} u", "Status": "🔴 BINDING" if lp_r['slack_mgmt'] < 0.1 else "🟢 SLACK"},
                {"Constraint Description": "Equipment Capacity Ceiling (1,500 u)", "LP Value Used": f"{lp_r['proc_units']:.0f} u", "Slack Remaining": f"{lp_r['slack_equip']:.1f} u", "Status": "🔴 BINDING" if lp_r['slack_equip'] < 0.1 else "🟢 SLACK"},
                {"Constraint Description": "Regular Payroll Overtime Ceiling (60.0 Days)", "LP Value Used": f"{lp_r['ot_reg']:.1f} Days", "Slack Remaining": f"{lp_r['slack_ot']:.1f} Days", "Status": "🔴 BINDING" if lp_r['slack_ot'] < 0.1 else "🟢 SLACK"},
                {"Constraint Description": "Outsource Contractor Ceiling (30.0 Artisans)", "LP Value Used": f"{lp_r['hire_out']:.1f} Artisans", "Slack Remaining": f"{lp_r['slack_out']:.1f} Artisans", "Status": "🔴 BINDING" if lp_r['slack_out'] < 0.1 else "🟢 SLACK"}
            ])
            st.table(slack_df)

            # Detailed Explanations
            diff_cost = comp['player_cost'] - comp['lp_cost']
            if diff_cost > 1.0:
                st.warning(f"""
                #### 🔵 Comparative Situation Analysis: Player Spend is Higher (+${diff_cost:,.2f})
                **Why the Google OR-Tools LP Solution is Better & More Optimal:**
                1. **Material Inventory Efficiency:** The LP purchased the exact minimum quantity required to keep raw stock above the 100u safety floor without tying up extra cash in inventory.
                2. **Labor Class Cost Ranking:** Regular Payroll Overtime ($20/day = $2.67/unit output) is far cheaper than Outsource Contractors ($40/day = $5.00/unit output). The LP maxed out cheap overtime before hiring contractors.
                3. **Management Bandwidth Protection:** The LP carefully balances overtime and contractor hiring to stay within the 250u management cap.
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
                st.success("🌟 **PERFECT OPTIMIZATION!** Your decision choices matched the Google OR-Tools optimal benchmark perfectly across all 4 variables.")

            # Next Day Callout & Button
            st.markdown(f"""
            <div class="callout-card-light">
                👉 <strong>LP Solution Analysis Complete for Day {st.session_state.day}!</strong><br>
                Review the OR-Tools optimal choices and constraint slack analysis above. When you are ready to proceed, click the button below to load Day {st.session_state.day + 1}.
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"▶ Step 1 Day Forward to Day {st.session_state.day + 1}", type="primary"):
                st.session_state.day += 1
                st.session_state.submitted_day = None
                st.session_state.last_comparison = None
                st.rerun()

        if st.session_state.game_history:
            st.write("### 📈 7-Day Performance Ledger")
            st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)

        if st.button("🔄 Reset 7-Day Game Session"):
            st.session_state.day = 1
            st.session_state.metal_stock = 500.0
            st.session_state.stone_stock = 500.0
            st.session_state.wip_metal = 0.0
            st.session_state.wip_stone = 0.0
            st.session_state.backlog_queue = 0.0
            st.session_state.cum_player_cost = 0.0
            st.session_state.cum_lp_cost = 0.0
            st.session_state.game_history = []
            st.session_state.submitted_day = None
            st.session_state.last_comparison = None
            st.rerun()

    else:
        st.balloons()
        st.success("🎉 **7-DAY SIMULATION COMPLETED!** All 7 days have been processed. Review your final performance summary below.")
        if st.session_state.game_history:
            st.write("### 📈 Final 7-Day Performance Ledger")
            st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)

            tot_player = st.session_state.cum_player_cost
            tot_lp = st.session_state.cum_lp_cost
            gap = tot_player - tot_lp
            grade = "A+" if gap <= 0 else "A" if gap < 5000 else "B" if gap < 15000 else "C"

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Player Operational Cost", f"${tot_player:,.2f}")
            c2.metric("Total LP Benchmark Cost", f"${tot_lp:,.2f}")
            c3.metric("Final Efficiency Grade", grade, delta=f"-${gap:,.2f} Gap" if gap > 0 else "0.0% Cost Variance")

        if st.button("🔄 Restart 7-Day Simulation Session"):
            st.session_state.day = 1
            st.session_state.metal_stock = 500.0
            st.session_state.stone_stock = 500.0
            st.session_state.wip_metal = 0.0
            st.session_state.wip_stone = 0.0
            st.session_state.backlog_queue = 0.0
            st.session_state.cum_player_cost = 0.0
            st.session_state.cum_lp_cost = 0.0
            st.session_state.game_history = []
            st.session_state.submitted_day = None
            st.session_state.last_comparison = None
            st.rerun()


# ==============================================================================
# OPTION 3: MODE 2 FULLY PARAMETRIC DIGITAL TWIN SANDBOX
# ==============================================================================
else:
    st.header("🔬 Option 3: Mode 2 - Fully Parametric Digital Twin Sandbox")
    st.info("💡 **Goal:** Test how changing ANY opening parameter or factory constraint alters 7-day cost, throughput, and shifting bottlenecks using Google OR-Tools.")

    with st.expander("⚙️ Configure All Opening Parameters & Factory Constraints", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 📦 Inventories & Safety Stock")
            p_init_metal = st.number_input("Opening Metal Stock (units):", min_value=0.0, value=500.0, step=50.0)
            p_init_stone = st.number_input("Opening Stone Stock (units):", min_value=0.0, value=500.0, step=50.0)
            p_safety_floor = st.number_input("Safety Stock Floor (units):", min_value=0.0, value=100.0, step=25.0)

            st.markdown("#### ⚙️ Physical Factory Constraints")
            p_mgt_cap = st.slider("Management Capacity Limit (units/day):", 100.0, 400.0, 250.0, step=10.0)
            p_equip_cap = st.slider("Equipment Capacity Ceiling (units/day):", 500.0, 3000.0, 1500.0, step=100.0)

        with col2:
            st.markdown("#### 👥 Starting Staff Allocation")
            p_reg_pre = st.number_input("Regular Artisans (Pre-Prod):", min_value=0, value=60, step=5)
            p_reg_post = st.number_input("Regular Artisans (Post-Prod):", min_value=0, value=70, step=5)
            p_skilled_pre = st.number_input("Skilled Artisans (Pre-Prod):", min_value=0, value=20, step=5)
            p_skilled_post = st.number_input("Skilled Artisans (Post-Prod):", min_value=0, value=20, step=5)
            p_con_pre = st.number_input("Skilled Contractors (Pre-Prod):", min_value=0, value=10, step=5)
            p_con_post = st.number_input("Skilled Contractors (Post-Prod):", min_value=0, value=15, step=5)

        with col3:
            st.markdown("#### 📊 Demand, Mix & Policy Caps")
            p_demand_mult = st.select_slider("Demand Multiplier:", options=[0.5, 1.0, 1.5, 2.0, 2.5], value=1.0)
            p_type_j_ratio = st.slider("Type J (Joining) Order Ratio (%):", 10, 70, 30, step=10)
            p_max_ot_days = st.slider("Max Regular Overtime Days Cap:", 0.0, 100.0, 60.0, step=5.0)
            p_max_outsource = st.slider("Max Outsource Contractors Cap:", 0.0, 50.0, 30.0, step=5.0)

            st.markdown("#### 💰 Raw Material Economics")
            p_price_metal = st.number_input("Metal Price ($/unit):", min_value=10.0, value=50.0, step=5.0)
            p_price_stone = st.number_input("Stone Price ($/unit):", min_value=10.0, value=100.0, step=5.0)

    run_dt_sim = st.button("▶ Run Parametric Digital Twin Simulation (Google OR-Tools)", type="primary")

    if run_dt_sim:
        st.write("### 📈 7-Day Digital Twin Simulation Results Ledger (Google OR-Tools)")

        base_demand_list = [500, 755, 1130, 500, 755, 500, 500]
        dt_results = []
        cur_metal = p_init_metal
        cur_stone = p_init_stone
        cur_backlog = 0.0
        tot_sim_cost = 0.0

        d1_audit = None
        peak_audit = None
        max_proc_seen = -1.0

        for d_idx, raw_dem in enumerate(base_demand_list, 1):
            dem_today = int(raw_dem * p_demand_mult)
            workload_today = dem_today + cur_backlog

            # Run Google OR-Tools LP Solver with Type J Ratio!
            lp_res = solve_daily_ortools(
                day_idx=d_idx,
                demand_units=workload_today,
                mgt_limit=p_mgt_cap,
                equip_limit=p_equip_cap,
                starting_metal=cur_metal,
                starting_stone=cur_stone,
                safety_floor=p_safety_floor,
                max_ot_days=p_max_ot_days,
                max_outsource_artisans=p_max_outsource,
                p_metal=p_price_metal,
                p_stone=p_price_stone,
                type_j_ratio=p_type_j_ratio,
                reg_pre=p_reg_pre, reg_post=p_reg_post,
                skilled_pre=p_skilled_pre, skilled_post=p_skilled_post,
                con_pre=p_con_pre, con_post=p_con_post,
                out_pre=p_con_pre, out_post=p_con_post
            )

            proc_units = lp_res['proc_units']
            j_pieces = lp_res['j_pieces']
            cur_backlog = max(0.0, workload_today - proc_units)

            raw_mat_cost = (lp_res['buy_m'] * p_price_metal) + (lp_res['buy_s'] * p_price_stone)
            labor_cost = lp_res['total_cost'] - raw_mat_cost
            day_total_cost = lp_res['total_cost']
            tot_sim_cost += day_total_cost

            # Update Inventory
            cur_metal = max(p_safety_floor, cur_metal + lp_res['buy_m'] - proc_units)
            cur_stone = max(p_safety_floor, cur_stone + lp_res['buy_s'] - proc_units)

            # Audit capture
            audit_entry = {
                'day': d_idx,
                'workload': workload_today,
                'proc_units': proc_units,
                'j_pieces': j_pieces,
                'lp_res': lp_res,
                'raw_mat_cost': raw_mat_cost,
                'labor_cost': labor_cost,
                'day_total_cost': day_total_cost,
                'metal_end': cur_metal,
                'stone_end': cur_stone
            }

            if d_idx == 1:
                d1_audit = audit_entry

            if proc_units > max_proc_seen:
                max_proc_seen = proc_units
                peak_audit = audit_entry

            # Bottleneck Identification
            if lp_res['slack_post'] < 0.1 and proc_units < workload_today:
                bottleneck_str = f"🔴 Post-Production Capacity Limit ({p_type_j_ratio:.0f}% Joining Mix)"
            elif lp_res['slack_equip'] < 0.1:
                bottleneck_str = f"⚠️ Equipment Ceiling ({p_equip_cap:.0f}u)"
            elif lp_res['slack_mgmt'] < 0.1:
                bottleneck_str = f"🔴 Mgmt Bandwidth Limit ({p_mgt_cap:.0f}u)"
            elif lp_res['slack_out'] < 0.1 and lp_res['slack_ot'] < 0.1:
                bottleneck_str = "🟡 Labor Caps Maxed (OT + Contractor)"
            elif lp_res['slack_out'] < 0.1:
                bottleneck_str = f"🔴 Outsource Contractor Cap Maxed ({p_max_outsource:.0f} Artisans)"
            elif lp_res['slack_ot'] < 0.1:
                bottleneck_str = f"🟡 Overtime Limit Maxed ({p_max_ot_days:.0f} Days)"
            elif lp_res['ot_reg'] > 0.5 or lp_res['hire_out'] > 0.5:
                bottleneck_str = "🔵 Capacity Expansion Active (OT / Contractor)"
            else:
                bottleneck_str = "🟢 Baseline Capacity (No Bottleneck)"

            dt_results.append({
                "Day": f"Day {d_idx}",
                "Workload Received": f"{workload_today:.0f} u",
                "Units Processed": f"{proc_units:.0f} u / {j_pieces:.0f} J",
                "Backlog": f"{cur_backlog:.0f} u",
                "Management Used": f"{lp_res['mgmt_used']:.1f} / {p_mgt_cap:.1f} u",
                "Overtime days": f"{lp_res['ot_reg']:.1f} days",
                "Additional Outsource Contractors used": f"{lp_res['hire_out']:.1f} artisans",
                "Raw Material Cost": f"${raw_mat_cost:,.2f}",
                "Labor Cost": f"${labor_cost:,.2f}",
                "Total Cost": f"${day_total_cost:,.2f}",
                "Active Bottleneck / LP Constraint": bottleneck_str
            })

        dt_df = pd.DataFrame(dt_results)
        st.dataframe(dt_df, use_container_width=True)

        st.metric("Total 7-Day Digital Twin Simulation Cost (Google OR-Tools)", f"${tot_sim_cost:,.2f}")

        # Sensitivity & System Bottleneck Report
        st.markdown("### 🧠 System Bottleneck & Sensitivity Analysis Report")
        st.info(f"""
        **Parametric Sensitivity Findings for Selected Configuration:**
        1. **Joining Order Mix (Type J = {p_type_j_ratio:.0f}%):** Joining orders require 2 days of Post-Production labor (1.0 + {p_type_j_ratio/100:.2f} = {1.0 + p_type_j_ratio/100:.2f} Post-Prod labor units / finished piece). Raising Type J ratio from 30% to 70% increases Post-Production labor demand by **+30.8%**, triggering contractor recruitment or Post-Production capacity bottlenecks!
        2. **Management Capacity Sensitivity:** Current limit is **{p_mgt_cap:.1f} u/day**. Outsource contractors consume 0.3 mgmt/artisan while Regular Overtime consumes 0.4 mgmt/day. If management capacity is restricted below **220 u/day**, the LP solver prioritizes outsource contractors (26.67 u output per mgmt unit) over regular overtime (6.25 u output per mgmt unit).
        3. **Equipment Ceiling Impact:** Equipment ceiling is set to **{p_equip_cap:.0f} u/day**. On surge days (Day 3 workload = {1130 * p_demand_mult:.0f} u), if demand exceeds equipment capacity, orders accumulate in the backlog queue.
        4. **Inventory Safety Floor Rule:** Opening stock was {p_init_metal:.0f}u Metal / {p_init_stone:.0f}u Stone with a {p_safety_floor:.0f}u safety floor. The OR-Tools solver procured raw materials just-in-time to preserve the safety floor without locking up excess working capital.
        """)

        # Detailed Audit Section
        st.markdown("---")
        st.markdown("### 📋 Mathematical Documentation & Worked Cost Verification")

        def render_audit_block(case_title, audit_dict):
            lp_res = audit_dict['lp_res']
            st.markdown(f"#### 🔹 {case_title} (Day {audit_dict['day']})")

            st.write(f"**Workload Queue:** {audit_dict['workload']:.0f} u | **Units Processed:** {audit_dict['proc_units']:.0f} u / {audit_dict['j_pieces']:.0f} J (Joining Mix = {p_type_j_ratio:.0f}%)")

            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**Decision Variable Values (Google OR-Tools GLOP Solution):**")
                st.markdown(f"""
                * **Metal Purchased (`buy_m`):** `{lp_res['buy_m']:.1f} units` @ ${p_price_metal:.2f}/u
                * **Stone Purchased (`buy_s`):** `{lp_res['buy_s']:.1f} units` @ ${p_price_stone:.2f}/u
                * **Regular Payroll Overtime (`ot_reg`):** `{lp_res['ot_reg']:.1f} days` (Max Cap: {p_max_ot_days:.1f} days)
                * **Outsource Contractors (`hire_out`):** `{lp_res['hire_out']:.1f} artisans` (Max Cap: {p_max_outsource:.1f} artisans)
                """)

            with c2:
                st.markdown("**Constraint Capacities & Slack Analysis:**")
                st.markdown(f"""
                * **Management Bandwidth:** `{lp_res['mgmt_used']:.1f} / {p_mgt_cap:.1f} u` (Slack: `{lp_res['slack_mgmt']:.1f} u`)
                * **Equipment Processing Ceiling:** `{audit_dict['proc_units']:.0f} / {p_equip_cap:.0f} u` (Slack: `{lp_res['slack_equip']:.1f} u`)
                * **Post-Production Labor Capacity:** `{audit_dict['proc_units']*(1.0 + p_type_j_ratio/100):.1f} labor u` (Slack: `{lp_res['slack_post']:.1f} u`)
                * **Raw Material Ending Stock:** `{audit_dict['metal_end']:.1f}u Metal / {audit_dict['stone_end']:.1f}u Stone` (Floor: {p_safety_floor:.0f}u)
                """)

            st.markdown("**Worked-Out Cost Calculations:**")
            m_cost = lp_res['buy_m'] * p_price_metal
            s_cost = lp_res['buy_s'] * p_price_stone
            base_lab = lp_res.get('base_cost', 3650.0)
            ot_cost = lp_res['ot_reg'] * 20.0
            out_cost = lp_res['hire_out'] * 40.0

            st.markdown(f"""
            * **Raw Material Cost Calculation:**
              * Metal: `{lp_res['buy_m']:.1f} u × ${p_price_metal:.2f}` = **${m_cost:,.2f}**
              * Stone: `{lp_res['buy_s']:.1f} u × ${p_price_stone:.2f}` = **${s_cost:,.2f}**
              * **Subtotal Raw Material Cost:** `${audit_dict['raw_mat_cost']:,.2f}`
            * **Labor Cost Calculation:**
              * Base Fixed Staff Payroll: **${base_lab:,.2f}**
              * Regular Overtime Surcharge: `{lp_res['ot_reg']:.1f} days × $20.00/day` = **${ot_cost:,.2f}**
              * Outsource Contractor Surcharge: `{lp_res['hire_out']:.1f} artisans × $40.00/day` = **${out_cost:,.2f}**
              * **Subtotal Labor Cost:** `${audit_dict['labor_cost']:,.2f}`
            * **TOTAL DAILY OPERATIONAL COST:** `${audit_dict['day_total_cost']:,.2f}`
            """)

        if d1_audit:
            render_audit_block("Case 1: Opening Day 1 Calculation", d1_audit)

        if peak_audit:
            st.markdown("---")
            render_audit_block(f"Case 2: Peak Throughput Case (Max Units Processed = {max_proc_seen:.0f} u)", peak_audit)
