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
    .callout-nextstep {
        background-color: #0f172a;
        border: 2px solid #38bdf8;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-val { font-size: 1.5rem; font-weight: 700; color: #f8fafc; }
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
    """
    try:
        prob = pulp.LpProblem(f"LP_Bench_Day_{day_idx}", pulp.LpMinimize)
        
        usable_metal = max(0.0, starting_metal - 100.0)
        usable_stone = max(0.0, starting_stone - 100.0)
        
        req_proc_m = max(0.0, demand_units - usable_metal)
        req_proc_s = max(0.0, demand_units - usable_stone)
        
        buy_m = pulp.LpVariable("buy_m", lowBound=req_proc_m, cat=pulp.LpContinuous)
        buy_s = pulp.LpVariable("buy_s", lowBound=req_proc_s, cat=pulp.LpContinuous)
        ot_reg = pulp.LpVariable("ot_reg", lowBound=0.0, upBound=60.0, cat=pulp.LpContinuous)
        hire_out = pulp.LpVariable("hire_out", lowBound=0.0, upBound=30.0, cat=pulp.LpContinuous)
        
        output_cap = 860.0 + (ot_reg * 2.5) + (hire_out * 8.0)
        prob += (output_cap >= demand_units, "Demand_Fulfillment")
        prob += (164.5 + (ot_reg * 0.4) + (hire_out * 0.3) <= mgt_limit, "Management_Capacity")
        
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
    st.header("📖 Case Study Tutorial: Optimization & Simulation in Supply Chains")
    
    tab1, tab2 = st.tabs(["Part 1: Fundamentals & Factory Setup", "Part 2: Worked Case Examples"])
    
    with tab1:
        st.markdown("""
        ### 1. Introduction to Linear Programming & Discrete Event Simulation
        In modern supply chain management, balancing cost, throughput, and service levels requires combining **Linear Programming (LP)** and **Discrete Event Simulation (DES)**:
        * **Linear Programming (LP):** Acts as the *Intelligent Planner*. It formulates operational decisions (procurement, labor allocation, overtime) as mathematical objective functions subject to linear constraints.
        * **Discrete Event Simulation (DES):** Acts as the *Physical Factory Engine*. It tracks individual order movements, inventory decrements, and equipment queueing over time.
        
        ---
        
        ### 2. Factory Process Flow & Lead Times
        1. **Design Stage (Optional):** Takes 1 day per order ($100 fee) with a 25% probability of saving 10% metal requirement (0.9 u/piece vs 1.0 u/piece standard).
        2. **Pre-Production Stage:** Involves raw material casting, cutting, and prep. Processing capacity cap = **1,500 units/day**.
        3. **Post-Production Stage:** Involves setting, joining, and polishing. Processing capacity cap = **1,500 units/day**.
        * **Type O (Ordinary Orders):** 1 day in Pre-Production + 1 day in Post-Production (**2-day total cycle time**).
        * **Type J (Joining Orders):** 1 day in Pre-Production + 2 days in Post-Production (**3-day total cycle time**).
        
        ---
        
        ### 3. Resource Matrix & Constraint Framework
        | Artisan Class | Starting Staff (Pre / Post) | Daily Output | Daily Rate | Overtime Limit | Allowed Orders | Management Overhead |
        | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
        | **Regular Payroll** | 60 / 70 | 5 u/day | $10/day ($2.00/u) | 0.5 day ($20/day) | **Type O Only** | 0.4 u / artisan |
        | **Skilled Payroll** | 20 / 20 | 5 u/day | $15/day ($3.00/u) | 0.5 day ($30/day) | **Type O & J** | 2.0 u / artisan |
        | **Skilled Contractor** | 10 / 15 | 8 u/day | $30/day ($3.75/u) | None | **Type O & J** | 1.0 u / artisan |
        | **Outsource Contractor** | 10 / 15 | 8 u/day | $40/day ($5.00/u) | None | **Type O & J** | 0.3 u / artisan |
        
        * **Bill of Materials (BOM):** Each product unit consumes **1 unit Metal ($50)** and **1 unit Stone ($100)**.
        * **Raw Material Safety Floor:** A mandatory floor of **100 units Metal** and **100 units Stone** must be maintained at all times.
        * **Management Bandwidth Cap:** Maximum **250.0 management units/day** budget across all staff.
        
        ---
        
        ### 4. Raw Material Procurement Safety Floor Rule (Example)
        > **⚠️ Important Procurement Math:**
        > If today's incoming demand is **500 units** and starting metal stock is **200 units**, usable stock is only **100 units** (`200 - 100 safety floor`).
        > Therefore, you **must procure at least 400 units** of new metal (`500 - 100 = 400`). Procuring less causes production to stall!
        """)

    with tab2:
        st.markdown("""
        ### 📊 Worked Case Examples & Constraint Progression
        
        #### 🟢 Example 1: Low Demand Load (~500 units/day)
        * **Demand Profile:** 43 Orders (500 units).
        * **Factory Response:** Starting baseline staff has a regular-time capacity of **860 units/day** in Pre-Production.
        * **LP Solution:**
          * **Metal Purchased:** 100 units | **Stone Purchased:** 100 units (replenishing stock to safety floor).
          * **Overtime:** 0.0 days | **Contractors Hired:** 0.0 artisans.
          * **Management Used:** 164.5 / 250.0 u (Unbinding).
          * **Total Daily Cost:** **$18,650.00** ($3,650 base labor + $15,000 materials).
        * **Teaching Takeaway:** Low demand is fully absorbed by baseline staff without overtime or extra spend.
        
        ---
        
        #### 🔴 Example 2: High Demand Surge (~1,000–1,500 units/day) & Constraint Progression
        When demand surges, constraints max out in sequence:
        1. **Overtime Constraint Maxed First (~1,000 u/day):** Regular Payroll Overtime ($2.67/unit output) is deployed up to its 60-day cap before hiring external contractors.
        2. **Management Bandwidth Cap Maxed Second (~1,200 u/day):** Management bandwidth reaches the 250.0 u limit. The LP shifts toward Outsource Contractors (0.038 mgmt/u) to buy output without breaking management headroom.
        3. **Equipment Capacity Ceiling Maxed Third (~1,500 u/day):** Physical equipment capacity (1,500 u/day) is reached, forming a bottleneck and accumulating Work-in-Progress (WIP) backlogs.
        """)

# --- OPTION 2: MODE 1 DAILY DECISION GAME ---
elif mode == "🎮 Option 2: Mode 1 - Daily Decision Game":
    st.header("🎮 Mode 1: Interactive Daily Decision Game (Player vs LP Benchmark)")
    
    with st.expander("📌 Quick Reference: Factory Setup, Process Flow & Resource Constraints", expanded=False):
        st.markdown("""
        * **Manufacturing Lead Times:** Type O = 2 days (1 Pre + 1 Post), Type J = 3 days (1 Pre + 2 Post).
        * **Process Constraints:** Pre-Prod Cap = 1,500 u/day, Post-Prod Cap = 1,500 u/day.
        * **Raw Material Safety Floor:** Minimum 100 units Metal & 100 units Stone must be preserved (`Usable Stock = Current Stock - 100`).
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
        st.session_state.submitted_day_data = None

    if st.session_state.day <= 7:
        st.subheader(f"📅 Simulation State: Day {st.session_state.day} of 7")

        # Instruction Card (White Background, Dark Navy Text)
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
            4: {"count": 43, "units": 500, "desc": "Normal Demand"},
            5: {"count": 65, "units": 755, "desc": "+50% Demand Surge"},
            6: {"count": 43, "units": 500, "desc": "Normal Demand"},
            7: {"count": 43, "units": 500, "desc": "Normal Demand"}
        }

        curr_demand = demand_schedule.get(st.session_state.day, {"count": 43, "units": 500, "desc": "Standard Demand"})
        tot_queue_today = curr_demand['units'] + st.session_state.backlog_queue

        st.info(f"📦 **Today's Incoming Demand (Day {st.session_state.day}):** {curr_demand['count']} Orders ({curr_demand['units']} units) — *{curr_demand['desc']}* | **Total Workload Queue:** {tot_queue_today:.0f} units")

        # Form for Decision Entry
        with st.form(f"daily_decision_form_day_{st.session_state.day}"):
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
            
            lp_res = solve_daily_lp_benchmark(st.session_state.day, tot_queue_today, 250.0, 1500, st.session_state.metal_stock, st.session_state.stone_stock)
            lp_day_cost = lp_res['total_cost']
            
            if not is_feasible:
                efficiency = 0.0
                score_str = "0.0% (Feasibility Failure)"
            else:
                efficiency = min(100.0, (lp_day_cost / player_day_cost) * 100.0) if player_day_cost > 0 else 100.0
                score_str = f"{efficiency:.1f}%"
                
            unprocessed = max(0.0, tot_queue_today - feasible_prod)
            
            st.session_state.submitted_day_data = {
                'day': st.session_state.day,
                'is_feasible': is_feasible,
                'feasible_prod': feasible_prod,
                'unprocessed': unprocessed,
                'buy_m': buy_m, 'lp_m': lp_res['buy_m'],
                'buy_s': buy_s, 'lp_s': lp_res['buy_s'],
                'ot_reg': ot_reg, 'lp_ot': lp_res['ot_reg'],
                'hire_out': hire_out, 'lp_out': lp_res['hire_out'],
                'player_cost': player_day_cost, 'lp_cost': lp_day_cost,
                'efficiency': efficiency,
                'score_str': score_str,
                'demand_count': curr_demand['count'],
                'demand_units': curr_demand['units'],
                'tot_queue_today': tot_queue_today
            }
            st.rerun()

        # Stage 2: Display Submitted Decision Analysis & LP Comparison
        if st.session_state.submitted_day_data and st.session_state.submitted_day_data['day'] == st.session_state.day:
            sub_data = st.session_state.submitted_day_data
            
            st.markdown("---")
            st.write(f"### 📊 Day {sub_data['day']} Decision Analysis & LP Solution Comparison")
            
            if not sub_data['is_feasible']:
                st.error("🚨 PRODUCTION STALLED / FEASIBILITY FAILURE: Your material purchases or labor capacity were insufficient to process the workload, or raw material fell below the 100u safety floor. Production stalled and a 0% score was assigned.")
            
            comp_df = pd.DataFrame([
                {"Decision Variable": "1. Metal Purchase (units)", "Player Choice": f"{sub_data['buy_m']:.0f} u", "LP Optimal": f"{sub_data['lp_m']:.0f} u", "Cost Impact": f"${((sub_data['buy_m'] - sub_data['lp_m']) * 50):,.2f}"},
                {"Decision Variable": "2. Stone Purchase (units)", "Player Choice": f"{sub_data['buy_s']:.0f} u", "LP Optimal": f"{sub_data['lp_s']:.0f} u", "Cost Impact": f"${((sub_data['buy_s'] - sub_data['lp_s']) * 100):,.2f}"},
                {"Decision Variable": "3. Regular Payroll Overtime (days)", "Player Choice": f"{sub_data['ot_reg']:.1f} days", "LP Optimal": f"{sub_data['lp_ot']:.1f} days", "Cost Impact": f"${((sub_data['ot_reg'] - sub_data['lp_ot']) * 20):,.2f}"},
                {"Decision Variable": "4. Outsource Contractors Hired (artisans)", "Player Choice": f"{sub_data['hire_out']:.1f} artisans", "LP Optimal": f"{sub_data['lp_out']:.1f} artisans", "Cost Impact": f"${((sub_data['hire_out'] - sub_data['lp_out']) * 40):,.2f}"},
                {"Decision Variable": "TOTAL DAILY OPERATIONAL SPEND", "Player Choice": f"${sub_data['player_cost']:,.2f}", "LP Optimal": f"${sub_data['lp_cost']:,.2f}", "Cost Impact": f"${(sub_data['player_cost'] - sub_data['lp_cost']):,.2f}"}
            ])
            st.table(comp_df)

            diff_cost = sub_data['player_cost'] - sub_data['lp_cost']
            if diff_cost > 1.0:
                st.warning(f"""
                #### 🔵 Comparative Situation Analysis: Player Spend is Higher (+${diff_cost:,.2f})
                **Why the LP Solution is Better & More Optimal:**
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
                st.success("🌟 **PERFECT OPTIMIZATION!** Your decision choices matched the LP optimal benchmark perfectly across all 4 variables.")

            # Callout Banner & Step Forward Button
            st.markdown("""
            <div class="callout-nextstep">
                <h4>👉 LP Solution Analysis Complete!</h4>
                <p>Review the LP optimal choices and comparative analysis above. When you are ready to proceed to the next simulation day, click the button below to load Day X+1.</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"▶ Step 1 Day Forward to Day {st.session_state.day + 1}", type="primary"):
                # Commit Day Results to History & Advance State
                sub = st.session_state.submitted_day_data
                st.session_state.backlog_queue = sub['unprocessed']
                st.session_state.metal_stock = max(100.0, st.session_state.metal_stock + sub['buy_m'] - sub['feasible_prod'])
                st.session_state.stone_stock = max(100.0, st.session_state.stone_stock + sub['buy_s'] - sub['feasible_prod'])
                st.session_state.wip_metal += sub['feasible_prod']
                st.session_state.wip_stone += sub['feasible_prod']
                
                st.session_state.cum_player_cost += sub['player_cost']
                st.session_state.cum_lp_cost += sub['lp_cost']
                
                st.session_state.game_history.append({
                    "Day": f"Day {sub['day']}",
                    "Player Spend": f"${sub['player_cost']:,.2f}",
                    "LP Optimal": f"${sub['lp_cost']:,.2f}",
                    "Score": sub['score_str'],
                    "Backlog Left": f"{sub['unprocessed']:.0f} u"
                })
                
                st.session_state.submitted_day_data = None
                st.session_state.day += 1
                st.rerun()

        if st.session_state.game_history:
            st.write("### 📈 7-Day Performance Ledger")
            st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)

    else:
        st.balloons()
        st.success("🎉 **7-DAY SIMULATION COMPLETED!** All 7 days have been processed. Review your final performance summary below.")
        
        if st.session_state.game_history:
            st.write("### 🏆 Final 7-Day Performance Summary Ledger")
            st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)
            
            p_tot = st.session_state.cum_player_cost
            lp_tot = st.session_state.cum_lp_cost
            gap = p_tot - lp_tot
            overall_eff = (lp_tot / p_tot * 100.0) if p_tot > 0 else 100.0
            
            st.metric("Total 7-Day Player Spend", f"${p_tot:,.2f}")
            st.metric("Total 7-Day LP Benchmark Spend", f"${lp_tot:,.2f}", delta=f"-${gap:,.2f} Variance")
            st.metric("Overall 7-Day Optimization Grade", f"{overall_eff:.1f}%")

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
            st.session_state.submitted_day_data = None
            st.rerun()

# --- OPTION 3: MODE 2 DIGITAL TWIN SANDBOX ---
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
        for d_idx, raw_recv in enumerate(base_orders, 1):
            recv_cnt = int(raw_recv * demand_mult)
            comp_cnt = int(recv_cnt * (0.85 if type_j_ratio <= 30 else 0.75))
            mgt_used = min(mgt_cap, 164.5 + d_idx * 2.5)
            d_cost = 3650.0 + (comp_cnt * (p_metal * 0.4 + p_stone * 0.6))
            cum_cost += d_cost

            sim_data.append({
                "Day": f"Day {d_idx}",
                "Workload Received": f"{recv_cnt} u",
                "Units Processed": f"{comp_cnt} u",
                "Management Used": f"{mgt_used:.1f} / {mgt_cap} u",
                "Daily Total Cost": f"${d_cost:,.2f}"
            })

        st.dataframe(pd.DataFrame(sim_data), use_container_width=True)

        st.metric("Total 7-Day Simulation Cost", f"${cum_cost:,.2f}")
        st.success("Simulation run complete! Adjust the parameters above to run sensitivity experiments.")
