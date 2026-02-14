import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from scipy.optimize import minimize

# --- 1. RISK DERIVATION UTILITY ---
def calculate_risk_index(df):
    """
    Calculates the AI Risk Index based on 3 pillars.
    Formula: 50% Geopolitics (Stability), 30% Logistics, 20% Complexity.
    """
    g_risk = 1 - (df["Stability"] / 10)
    l_risk = 1 - (df["Logistics"] / 10)
    c_risk = df["Complexity"] / 10
    return round((g_risk * 0.5) + (l_risk * 0.3) + (c_risk * 0.2), 2)

# --- 2. CORE AI ENGINE ---
def run_optimization_engine(total_demand, countries, tariffs, prices, risks, force_mix):
    num_countries = len(countries)
    initial_guess = [total_demand / num_countries] * num_countries
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - total_demand})
    bounds = [(total_demand * 0.05, total_demand) if force_mix else (0, total_demand) for _ in range(num_countries)]
    
    def objective_function(volumes):
        total_cost = 0
        for i in range(num_countries):
            unit_landed = prices[i] * (1 + tariffs[i])
            total_cost += (volumes[i] * unit_landed) * (1 + risks[i])
        return total_cost

    result = minimize(objective_function, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    return result.x

# --- 3. UI SETUP ---
st.set_page_config(page_title="Techylla AI Optimizer", layout="wide")

l_col, c_col, r_col = st.columns([1, 2, 1])
with c_col:
    if os.path.exists("techyllalogo.png"):
        st.image("techyllalogo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #1E40AF;'>TECHYLLA AI</h1>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>AI Sourcing Command Center</h2>", unsafe_allow_html=True)
st.write("---")

# --- 4. DATA INITIALIZATION ---
if 'market_df' not in st.session_state:
    initial_data = {
        "Country": ["India (IN)", "China (CN)", "Mexico (MX)", "Canada (CA)", "Belgium (BE)", "USA (US)"],
        "Unit_Price": [2100, 1950, 2250, 2300, 2150, 2400],
        "Tariff_Rate": [0.05, 0.30, 0.00, 0.00, 0.06, 0.00],
        "Stability": [7, 4, 7, 9, 8, 9],
        "Logistics": [6, 8, 7, 9, 9, 9],
        "Complexity": [5, 7, 4, 2, 3, 1]
    }
    temp_df = pd.DataFrame(initial_data)
    # Generate the index column immediately
    temp_df["AI_Risk_Index"] = temp_df.apply(calculate_risk_index, axis=1)
    st.session_state.market_df = temp_df

# --- 5. SIDEBAR & EDITOR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    total_qty = st.number_input("Annual Demand (MT)", value=10000)
    risk_sensitivity = st.slider("Risk Weighting", 0.0, 2.0, 1.0)
    force_mix = st.checkbox("Force Diversification (Min 5%)", value=False)

st.write("### 🌐 Market Intelligence Feed")
# We allow the table to be edited, and the Risk Index column will update on the next interaction
edited_df = st.data_editor(st.session_state.market_df, use_container_width=True, hide_index=True)

# Update the Risk Index based on the new user inputs in the table
edited_df["AI_Risk_Index"] = edited_df.apply(calculate_risk_index, axis=1)

# --- 6. EXECUTION ---
if st.button("🚀 Run Full AI Analysis"):
    with st.spinner("Optimizing Supply Chain..."):
        # Run AI Solver
        res = run_optimization_engine(
            total_qty, 
            edited_df["Country"].tolist(), 
            edited_df["Tariff_Rate"].tolist(),
            edited_df["Unit_Price"].tolist(), 
            (edited_df["AI_Risk_Index"] * risk_sensitivity).tolist(), 
            force_mix
        )
        
        # Financials
        edited_df["Optimized_Volume"] = res
        edited_df["Landed_Cost"] = edited_df["Unit_Price"] * (1 + edited_df["Tariff_Rate"])
        edited_df["Risk_Premium"] = edited_df["Landed_Cost"] * (edited_df["AI_Risk_Index"] * risk_sensitivity)
        edited_df["Effective_Unit_Cost"] = edited_df["Landed_Cost"] + edited_df["Risk_Premium"]
        
        total_cost = (edited_df["Optimized_Volume"] * edited_df["Landed_Cost"]).sum()
        savings = (total_qty * edited_df["Landed_Cost"].mean()) - total_cost

        # --- OUTPUT DISPLAY ---
        st.write("---")
        k1, k2, k3 = st.columns(3)
        k1.metric("Optimized Landed Cost", f"${total_cost:,.0f}")
        k2.metric("Projected Savings", f"${savings:,.0f}")
        k3.metric("Volume Targeted", f"{total_qty:,.0f} MT")

        c1, c2 = st.columns([1.2, 1])
        with c1:
            fig = px.pie(edited_df[edited_df["Optimized_Volume"] > 0.1], values='Optimized_Volume', names='Country', 
                         title="AI Sourcing Allocation", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.write("### 🎯 Allocation Details")
            st.dataframe(edited_df[edited_df["Optimized_Volume"] > 0.1][["Country", "Optimized_Volume"]]
                         .style.format({"Optimized_Volume": "{:,.0f} MT"}), use_container_width=True)

        st.write("---")
        st.subheader("💡 AI Strategic Rationale & Mathematical Proof")
        st.info(f"The AI prioritized **{edited_df.loc[edited_df['Optimized_Volume'].idxmax()]['Country']}** due to the lowest Effective Unit Cost.")
        
        # This shows the final math with the visible Risk Index
        st.table(edited_df[["Country", "AI_Risk_Index", "Landed_Cost", "Risk_Premium", "Effective_Unit_Cost"]].sort_values("Effective_Unit_Cost").style.format({
            "AI_Risk_Index": "{:.2f}", "Landed_Cost": "${:,.2f}", "Risk_Premium": "+${:,.2f}", "Effective_Unit_Cost": "${:,.2f}"
        }))