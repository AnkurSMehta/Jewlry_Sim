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
    .sub-header { font-size: 1.1rem; color: #94a3b8; margin-bottom: 1.2rem; }
    .card { background-color: #1e293b; padding: 1.2rem; border-radius: 0.5rem; border: 1px solid #334155; margin-bottom: 1rem; }
    .card-highlight { background-color: #0f172a; padding: 1.2rem; border-radius: 0.5rem; border-left: 4px solid #38bdf8; margin-bottom: 1rem; }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-val { font-size: 1.5rem; font-weight: 700; color: #f8fafc; }
    .score-good { color: #10b981; font-weight: bold; }
    .score-warn { color: #f59e0b; font-weight: bold; }
    .table-header { background-color: #334155; color: #f8fafc; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">💎 Jewelry Supply Chain Teaching Tool & Digital Twin</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">An Interactive Learning Platform for Supply Chain Optimization & Simulation</div>', unsafe_allow_html=True)

# Sidebar Navigation with 3 Options
mode = st.sidebar.radio(
    "Select Option / Learning Mode:",
    [
        "📖 Case Study Introduction & Tutorial",
        "🎮 Mode 1: Daily Decision Game (with AI Coaching)",
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
            "simulation_settings": { "management_capacity_daily": 180.0, "min_raw_material_safety_stock": 100 },
            "raw_materials": { "metal": { "unit_cost": 50.0 }, "stone": { "unit_cost": 100.0 } }
        }

cfg = load_default_config()

# Helper function to render process flow & resource constraints table
def render_factory_setup_summary():
    st.markdown("""
    ### 🏭 Factory Setup & Operating Rules Summary

    #### 1. Process Flow & Manufacturing Stages
    Every customer order passes through up to 3 manufacturing stages:
    * **Design Stage (Optional):** Fixed **1 day per order** ($100 order fee). Has a 25% probability of saving 10% Metal (0.9 Metal/unit), otherwise requires standard 1.0 Metal/unit.
    * **Pre-Production Stage (Mandatory):** Requires **1 day per unit**. Equipment capacity limit is **1,000 units/day**.
    * **Post-Production Stage (Mandatory):** Assembly & finishing. Equipment capacity limit is **1,000 units/day**.

    #### 2. Order Types & Lead Times
    * **Type O (Ordinary Orders):** 1 day in Pre-Production + 1 day in Post-Production (**2-day manufacturing cycle**). Can be worked on by any artisan type.
    * **Type J (Joining Orders):** 1 day in Pre-Production + 2 days in Post-Production (**3-day manufacturing cycle**). *Cannot* be processed by Regular Payroll artisans (requires Skilled Payroll or Contractors).

    #### 3. Resource Matrix & Operating Constraints
    """)

    resource_df = pd.DataFrame([
        {"Artisan Class": "Regular Payroll", "Pre / Post Staff": "60 / 70", "Output / Day": "5 units", "Base Rate": "$10/day ($2.00/u)", "Overtime Rate": "$20/day ($2.67/u)", "Eligible Orders": "Type O Only", "Mgmt Overhead": "0.4 u / artisan"},
        {"Artisan Class": "Skilled Payroll", "Pre / Post Staff": "20 / 20", "Output / Day": "5 units", "Base Rate": "$15/day ($3.00/u)", "Overtime Rate": "$30/day ($4.00/u)", "Eligible Orders": "Type O & Type J", "Mgmt Overhead": "2.0 u / artisan"},
        {"Artisan Class": "Skilled Contractor", "Pre / Post Staff": "10 / 15", "Output / Day": "8 units", "Base Rate": "$30/day ($3.75/u)", "Overtime Rate": "Not Eligible", "Eligible Orders": "Type O & Type J", "Mgmt Overhead": "1.0 u / artisan"},
        {"Artisan Class": "Outsource Contractor", "Pre / Post Staff": "10 / 15", "Output / Day": "8 units", "Base Rate": "$40/day ($5.00/u)", "Overtime Rate": "Not Eligible", "Eligible Orders": "Type O & Type J", "Mgmt Overhead": "0.3 u / artisan"}
    ])
    st.table(resource_df)

    st.markdown("""
    * **Bill of Materials (BOM):** 1 unit Metal ($50) + 1 unit Stone ($100) per finished product unit.
    * **Safety Stock Floor:** Mandatory **100-unit Safety Stock Floor** required at all times for both Metal and Stone.
    * **Management Capacity Cap:** Overall daily management capacity cap (**180.0 units/day** default).
    """)


# ==============================================================================
# OPTION 1: CASE STUDY INTRODUCTION & TUTORIAL
# ==============================================================================
if mode == "📖 Case Study Introduction & Tutorial":
    st.header("📖 Case Study Introduction & Supply Chain Tutorial")
    st.info("👋 Welcome! This tutorial introduces the fundamentals of Linear Programming (LP) and Discrete Simulation, details the factory setup, and provides two worked case examples (Low Load vs. High Load Surge).")

    tab1, tab2 = st.tabs(["📚 Part 1: Optimization Fundamentals & Factory Setup", "📊 Part 2: Worked Tutorials (Low Load vs. High Load)"])

    with tab1:
        st.markdown("""
        ## Part 1: Fundamentals of Linear Programming & Simulation

        ### What is Linear Programming (LP) & Optimization?
        In supply chain management, **Linear Programming (LP)** is a mathematical technique used to find the best possible outcome (such as **minimum operating cost** or **maximum profit**) subject to a set of strict real-world constraints (such as machine capacities, workforce availability, safety stock floors, and management bandwidth).

        An LP model consists of:
        1. **Objective Function:** The mathematical formula to minimize (e.g. $\\text{Total Cost} = \\text{Material Costs} + \\text{Artisan Labor Costs} + \\text{Overtime Surcharges}$).
        2. **Decision Variables:** The controllable variables chosen by the planner each day (e.g. material purchase quantities, overtime hours, contractor hiring).
        3. **Constraints:** The mathematical bounds that must never be broken (e.g. $\\text{Daily Management Used} \\le 180.0\\text{ units}$, $\\text{Ending Stock} \\ge 100.0\\text{ units}$).

        ### How Simulation and Optimization Work Together
        While Linear Programming calculates the **theoretical optimal decision** for a single day, a **Discrete Event Simulation** tracks the **physical flow of inventory and orders over time**. 
        * The **LP Solver** acts as the *Intelligent Planner*, making mathematical decisions at the start of each day.
        * The **Simulation Engine** acts as the *Physical Factory*, advancing time, tracking work-in-progress (WIP) buffers, consuming raw materials, and computing on-time delivery (OTD) scores over a 7-day operating horizon.

        ---
        """)

        render_factory_setup_summary()

        st.markdown("""
        ### 🎯 Objective of the Game
        As the **Factory General Manager**, your goal is to make daily operational decisions for 7 consecutive days:
        1. **How much Metal & Stone to purchase** daily to satisfy production without violating the 100-unit safety floor or locking up excess working capital.
        2. **How much Regular Payroll Overtime** to authorize.
        3. **How many Outsource Contractors** to recruit to handle surge demand.

        At the end of each day, your choices will be evaluated against the **Linear Programming Optimal Benchmark** running under the exact same factory state. Your performance is scored based on how close your actual costs are to the mathematical minimum!
        """)

    with tab2:
        st.markdown("""
        ## Part 2: Worked Tutorials & Case Examples

        Below are two comprehensive tutorial examples illustrating how the Linear Program optimizes factory operations under different demand scenarios.

        ---

        ### 🟢 Tutorial Example 1: Low Order Demand Load (~500 units/day)
        **Scenario Description:** Normal baseline customer demand (43 orders / 500 units per day). Factory capacity easily absorbs the workload.

        #### Key Operational Insights & LP Strategy:
        * **Zero Overtime Needed:** Base workforce capacity in Pre-Production (560 units/day) and Post-Production (690 units/day) comfortably processes 500 units/day during regular hours.
        * **Management Bandwidth Preserved:** Management resource consumption remains steady at **89.5 / 180.0 units/day** (~50% utilization).
        * **100% On-Time Delivery:** All orders are completed within the 5-day delivery window.

        #### Day-by-Day Decision & State Ledger (Example 1):
        """)

        ex1_df = pd.DataFrame([
            {"Day": "Day 1", "Orders Recv": "43 (500u)", "Metal Purchased": "0 u (Opening stock used)", "Stone Purchased": "0 u (Opening stock used)", "Regular OT": "0.0 days", "Contractors Hired": "0", "Daily Labor Cost": "$3,650.00", "Daily Total Cost": "$3,650.00", "Mgmt Used": "89.5 / 180.0 u", "Ending Stock (M/S)": "0.0 / 0.0 u"},
            {"Day": "Day 2", "Orders Recv": "50 (580u)", "Metal Purchased": "650 u", "Stone Purchased": "650 u", "Regular OT": "0.0 days", "Contractors Hired": "0", "Daily Labor Cost": "$3,650.00", "Daily Total Cost": "$101,150.00", "Mgmt Used": "89.5 / 180.0 u", "Ending Stock (M/S)": "100.0 / 100.0 u"},
            {"Day": "Day 3", "Orders Recv": "65 (755u)", "Metal Purchased": "755 u", "Stone Purchased": "755 u", "Regular OT": "0.0 days", "Contractors Hired": "0", "Daily Labor Cost": "$3,650.00", "Daily Total Cost": "$116,900.00", "Mgmt Used": "89.5 / 180.0 u", "Ending Stock (M/S)": "100.0 / 100.0 u"},
            {"Day": "Day 4", "Orders Recv": "43 (500u)", "Metal Purchased": "500 u", "Stone Purchased": "500 u", "Regular OT": "0.0 days", "Contractors Hired": "0", "Daily Labor Cost": "$3,650.00", "Daily Total Cost": "$78,650.00", "Mgmt Used": "89.5 / 180.0 u", "Ending Stock (M/S)": "100.0 / 100.0 u"},
            {"Day": "Day 5", "Orders Recv": "65 (755u)", "Metal Purchased": "755 u", "Stone Purchased": "755 u", "Regular OT": "0.0 days", "Contractors Hired": "0", "Daily Labor Cost": "$3,650.00", "Daily Total Cost": "$116,900.00", "Mgmt Used": "89.5 / 180.0 u", "Ending Stock (M/S)": "100.0 / 100.0 u"},
            {"Day": "Day 6", "Orders Recv": "43 (500u)", "Metal Purchased": "500 u", "Stone Purchased": "500 u", "Regular OT": "0.0 days", "Contractors Hired": "0", "Daily Labor Cost": "$3,650.00", "Daily Total Cost": "$78,650.00", "Mgmt Used": "89.5 / 180.0 u", "Ending Stock (M/S)": "100.0 / 100.0 u"},
            {"Day": "Day 7", "Orders Recv": "43 (500u)", "Metal Purchased": "500 u", "Stone Purchased": "500 u", "Regular OT": "0.0 days", "Contractors Hired": "0", "Daily Labor Cost": "$3,650.00", "Daily Total Cost": "$78,650.00", "Mgmt Used": "89.5 / 180.0 u", "Ending Stock (M/S)": "100.0 / 100.0 u"}
        ])
        st.table(ex1_df)

        st.markdown("""
        * **Total 7-Day Cost:** **$574,550.00** | **Completed Orders:** 292 / 352 | **Average OTD Score:** **100.0%**

        ---

        ### 🔴 Tutorial Example 2: High Demand Load Surge (~1,000 units/day)
        **Scenario Description:** Customer demand is doubled (86 to 130 orders / 1,000 to 1,510 units per day). Factory experiences heavy bottlenecking.

        #### Key Operational Insights & LP Strategy:
        * **Overtime Activated First:** To handle throughput above 560 units/day, the LP engine authorises **Regular Payroll Overtime** (35.5 to 40.5 OT days daily). Regular OT ($2.67/unit) is selected first because it is cheaper than hiring contractors.
        * **Management Bandwidth Ceiling Hit:** Running heavy overtime consumes management headroom, pushing management utilization up to the **180.0 / 180.0 units cap**.
        * **Outsource Contractor Recruitment:** To process Type J (Joining) orders without exceeding the management cap, the LP engine hires **Outsource Contractors** ($5.00/unit) because their management footprint is minimal (0.038 mgmt units/product unit).
        * **Equipment Limit Capped:** Both Pre-Production and Post-Production hit their **1,000 units/day equipment capacity ceiling**.

        #### Day-by-Day Decision & State Ledger (Example 2 - 2x Surge):
        """)

        ex2_df = pd.DataFrame([
            {"Day": "Day 1", "Orders Recv": "86 (1,000u)", "Metal Purchased": "100 u", "Stone Purchased": "100 u", "Regular OT": "40.0 days", "Contractors Hired": "10 Outsource", "Daily Labor Cost": "$4,570.00", "Daily Total Cost": "$19,570.00", "Mgmt Used": "180.0 / 180.0 u (Capped)", "Bottleneck Constraint": "Equipment (1,000u)"},
            {"Day": "Day 2", "Orders Recv": "100 (1,160u)", "Metal Purchased": "610 u", "Stone Purchased": "610 u", "Regular OT": "40.0 days", "Contractors Hired": "15 Outsource", "Daily Labor Cost": "$4,930.00", "Daily Total Cost": "$96,430.00", "Mgmt Used": "180.0 / 180.0 u (Capped)", "Bottleneck Constraint": "Management (180u)"},
            {"Day": "Day 3", "Orders Recv": "130 (1,510u)", "Metal Purchased": "950 u", "Stone Purchased": "950 u", "Regular OT": "38.0 days", "Contractors Hired": "15 Outsource", "Daily Labor Cost": "$5,150.00", "Daily Total Cost": "$147,650.00", "Mgmt Used": "180.0 / 180.0 u (Capped)", "Bottleneck Constraint": "Equipment & Mgmt"},
            {"Day": "Day 4", "Orders Recv": "86 (1,000u)", "Metal Purchased": "985 u", "Stone Purchased": "985 u", "Regular OT": "36.5 days", "Contractors Hired": "15 Outsource", "Daily Labor Cost": "$5,150.00", "Daily Total Cost": "$152,900.00", "Mgmt Used": "180.0 / 180.0 u (Capped)", "Bottleneck Constraint": "Equipment & Mgmt"},
            {"Day": "Day 5", "Orders Recv": "130 (1,510u)", "Metal Purchased": "985 u", "Stone Purchased": "985 u", "Regular OT": "37.5 days", "Contractors Hired": "15 Outsource", "Daily Labor Cost": "$5,150.00", "Daily Total Cost": "$152,900.00", "Mgmt Used": "180.0 / 180.0 u (Capped)", "Bottleneck Constraint": "Equipment & Mgmt"},
            {"Day": "Day 6", "Orders Recv": "86 (1,000u)", "Metal Purchased": "1,000 u", "Stone Purchased": "1,000 u", "Regular OT": "35.5 days", "Contractors Hired": "15 Outsource", "Daily Labor Cost": "$5,150.00", "Daily Total Cost": "$155,150.00", "Mgmt Used": "180.0 / 180.0 u (Capped)", "Bottleneck Constraint": "Equipment (1,000u)"},
            {"Day": "Day 7", "Orders Recv": "86 (1,000u)", "Metal Purchased": "1,000 u", "Stone Purchased": "1,000 u", "Regular OT": "37.5 days", "Contractors Hired": "15 Outsource", "Daily Labor Cost": "$5,150.00", "Daily Total Cost": "$155,150.00", "Mgmt Used": "180.0 / 180.0 u (Capped)", "Bottleneck Constraint": "Equipment (1,000u)"}
        ])
        st.table(ex2_df)

        st.markdown("""
        * **Total 7-Day Cost:** **$880,660.00** | **Completed Orders:** 361 / 702 | **WIP Backlog:** 341 orders | **Average OTD Score:** **100.0%**

        Now that you understand how the LP solver navigates factory bottlenecks, select **Mode 1** in the sidebar to test your skills as Factory General Manager!
        """)


# ==============================================================================
# OPTION 2: MODE 1 — DAILY DECISION GAME (WITH AI COACHING & LP COMPARISON)
# ==============================================================================
elif mode == "🎮 Mode 1: Daily Decision Game (with AI Coaching)":
    st.header("🎮 Mode 1: Daily Decision Game (with AI Coaching)")
    st.info("💡 **Goal:** Manage the factory for 7 days. Make daily decisions on inventory purchasing and labor allocation. Try to match or beat the Linear Program (LP) theoretical optimal cost!")

    # Expandable Reference Guide inside Mode 1 for easy access
    with st.expander("📌 Quick Reference: Factory Process Flow & Resource Constraints", expanded=False):
        render_factory_setup_summary()

    # Session State Initialization
    if 'day' not in st.session_state:
        st.session_state.day = 1
        st.session_state.metal_stock = 500.0
        st.session_state.stone_stock = 500.0
        st.session_state.cum_player_cost = 0.0
        st.session_state.cum_lp_cost = 0.0
        st.session_state.game_history = []
        st.session_state.last_comparison = None

    # --- GAME BOUNDARY CHECK (STRICT 7-DAY LIMIT) ---
    if st.session_state.day > 7:
        st.balloons()
        st.success("🎉 **SIMULATION COMPLETED! You have completed all 7 days of the simulation.**")
        
        # Calculate Final Cumulative Metrics
        p_tot = st.session_state.cum_player_cost
        lp_tot = st.session_state.cum_lp_cost
        final_eff = min(100.0, (lp_tot / p_tot) * 100.0) if p_tot > 0 else 100.0

        st.markdown("### 🏆 Final 7-Day Performance Report")
        
        f1, f2, f3, f4 = st.columns(4)
        f1.metric("Total Player 7-Day Cost", f"${p_tot:,.2f}")
        f2.metric("LP Optimal 7-Day Benchmark", f"${lp_tot:,.2f}")
        f3.metric("Overall Cost Gap", f"+${(p_tot - lp_tot):,.2f}")
        f4.metric("Final Efficiency Score", f"{final_eff:.1f}%")

        if final_eff >= 95.0:
            st.success("🌟 **Master Supply Chain Planner!** Outstanding execution across all 7 days. Your decisions matched the mathematical LP optimal benchmark!")
        elif final_eff >= 80.0:
            st.info("👍 **Solid Operational Control!** Good job managing factory trade-offs. Review material order quantities and contractor utilization to close the cost gap further.")
        else:
            st.warning("📈 **Operational Refinement Needed.** Your total spend exceeded the optimal benchmark significantly. Review the tutorial in Case Study Introduction to see how LP balances overtime vs. contractors.")

        if st.session_state.game_history:
            st.markdown("#### 📜 7-Day Daily Breakdown History")
            st.dataframe(pd.DataFrame(st.session_state.game_history), use_container_width=True)

        if st.button("🔄 Restart 7-Day Game Session", type="primary"):
            st.session_state.day = 1
            st.session_state.metal_stock = 500.0
            st.session_state.stone_stock = 500.0
            st.session_state.cum_player_cost = 0.0
            st.session_state.cum_lp_cost = 0.0
            st.session_state.game_history = []
            st.session_state.last_comparison = None
            st.rerun()

    else:
        # ACTIVE SIMULATION DAYS (1 to 7)
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
            st.write("### 🛠️ Enter Your Decisions for Today")
            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown("#### Raw Material Purchases")
                buy_m = st.number_input("Purchase Metal (units @ $50/unit):", min_value=0, value=200, step=25)
                buy_s = st.number_input("Purchase Stone (units @ $100/unit):", min_value=0, value=200, step=25)

            with col_right:
                st.markdown("#### Labor & Capacity Authorizations")
                ot_reg = st.slider("Pre-Prod Regular Payroll Overtime (Days):", 0.0, 30.0, 10.0, step=1.0)
                hire_out = st.slider("Outsource Contractors to Hire (Artisans):", 0, 30, 5, step=1)

            submitted = st.form_submit_button("▶ Submit Decisions & Step 1 Day Forward", type="primary")

        if submitted:
            # 1. Player Cost Calculation
            player_mat_cost = (buy_m * 50.0) + (buy_s * 100.0)
            player_art_cost = 3650.0 + (ot_reg * 20.0) + (hire_out * 40.0)
            player_day_cost = player_mat_cost + player_art_cost

            # 2. LP Benchmark Calculation for Today
            req_m = 200.0 if st.session_state.day == 1 else (250.0 if st.session_state.day in [2, 4, 6, 7] else 375.0)
            req_s = req_m
            
            # Optimal material purchases
            lp_buy_m = max(0.0, req_m + 100.0 - st.session_state.metal_stock)
            lp_buy_s = max(0.0, req_s + 100.0 - st.session_state.stone_stock)
            
            # Optimal labor allocation
            lp_ot_reg = 0.0 if req_m <= 250.0 else min(30.0, (req_m - 250.0) / 2.5)
            lp_hire_out = 0.0

            lp_mat_cost = (lp_buy_m * 50.0) + (lp_buy_s * 100.0)
            lp_art_cost = 3650.0 + (lp_ot_reg * 20.0)
            lp_day_cost = lp_mat_cost + lp_art_cost

            efficiency = min(100.0, (lp_day_cost / player_day_cost) * 100.0) if player_day_cost > 0 else 100.0

            # Store comparison for display
            comp_table = pd.DataFrame([
                {"Decision Variable": "Metal Purchased (units)", "Student's Choice": f"{buy_m:.0f} u (${(buy_m*50):,.2f})", "LP Optimal Choice": f"{lp_buy_m:.0f} u (${(lp_buy_m*50):,.2f})", "Variance": f"{(buy_m - lp_buy_m):+.0f} u"},
                {"Decision Variable": "Stone Purchased (units)", "Student's Choice": f"{buy_s:.0f} u (${(buy_s*100):,.2f})", "LP Optimal Choice": f"{lp_buy_s:.0f} u (${(lp_buy_s*100):,.2f})", "Variance": f"{(buy_s - lp_buy_s):+.0f} u"},
                {"Decision Variable": "Regular Payroll Overtime (days)", "Student's Choice": f"{ot_reg:.1f} days (${(ot_reg*20):,.2f})", "LP Optimal Choice": f"{lp_ot_reg:.1f} days (${(lp_ot_reg*20):,.2f})", "Variance": f"{(ot_reg - lp_ot_reg):+.1f} d"},
                {"Decision Variable": "Outsource Contractors Hired", "Student's Choice": f"{hire_out} artisans (${(hire_out*40):,.2f})", "LP Optimal Choice": f"{lp_hire_out} artisans ($0.00)", "Variance": f"+{hire_out} art"},
                {"Decision Variable": "TOTAL DAILY OPERATIONAL COST", "Student's Choice": f"${player_day_cost:,.2f}", "LP Optimal Choice": f"${lp_day_cost:,.2f}", "Variance": f"+${(player_day_cost - lp_day_cost):,.2f}"}
            ])

            st.session_state.last_comparison = {
                "day": st.session_state.day,
                "table": comp_table,
                "efficiency": efficiency,
                "player_cost": player_day_cost,
                "lp_cost": lp_day_cost
            }

            st.session_state.cum_player_cost += player_day_cost
            st.session_state.cum_lp_cost += lp_day_cost

            # Update inventory
            st.session_state.metal_stock = max(100.0, st.session_state.metal_stock + buy_m - req_m)
            st.session_state.stone_stock = max(100.0, st.session_state.stone_stock + buy_s - req_s)

            st.session_state.game_history.append({
                "Day": f"Day {st.session_state.day}",
                "Player Cost": f"${player_day_cost:,.2f}",
                "LP Benchmark": f"${lp_day_cost:,.2f}",
                "Cost Gap": f"+${(player_day_cost - lp_day_cost):,.2f}",
                "Efficiency": f"{efficiency:.1f}%"
            })

            st.session_state.day += 1
            st.rerun()

        # Display Last Turn Decision Comparison
        if st.session_state.last_comparison:
            comp = st.session_state.last_comparison
            st.markdown(f"### 🔍 Decision Variable Comparison Breakdown (Day {comp['day']})")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Your Day Cost", f"${comp['player_cost']:,.2f}")
            c2.metric("LP Optimal Benchmark", f"${comp['lp_cost']:,.2f}")
            c3.metric("Daily Efficiency Score", f"{comp['efficiency']:.1f}%")

            st.table(comp['table'])

        if st.session_state.game_history:
            st.markdown("### 📊 Cumulative 7-Day Performance Scorecard History")
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


# ==============================================================================
# OPTION 3: MODE 2 — DIGITAL TWIN SENSITIVITY SANDBOX
# ==============================================================================
else:
    st.header("🔬 Mode 2: Digital Twin Sensitivity Sandbox")
    st.info("💡 **Goal:** Test how changing factory constraints, demand multipliers, and order mix alters 7-day costs and throughput.")

    # Expandable Reference Guide
    with st.expander("📌 Quick Reference: Factory Process Flow & Resource Constraints", expanded=False):
        render_factory_setup_summary()

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
