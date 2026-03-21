import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from google import genai
import json

# --- 1. CONFIG & KEYS ---
# Note: Using gemini-2.0-flash as requested (2.5 is not yet a standard release)
GEMINI_API_KEY = "AIzaSyCqVtS2jrzCZef_4RbEu1Qo3F_4HIp7DGg"
TAVILY_API_KEY = "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"
client_gemini = genai.Client(api_key=GEMINI_API_KEY)

# --- 2. ENHANCED DATA GENERATOR (Realistic Indorama Portfolio) ---
@st.cache_data
def load_indorama_erp_realistic():
    fgs = ["RAMAPET Resin", "High-Tenacity Rayon", "Polyester Fiber"]
    rms = ["PTA", "MEG", "PX", "rPET", "Ethylene", "Natural Gas", "Electricity", "Acetic Acid", 
           "Methanol", "Isophthalic Acid", "Catalyst-A", "Titanium Dioxide", "Spin Finish", 
           "Pallets", "Shrink Wrap", "Nitrogen", "Hydrogen", "Process Water", "Fuel Oil", "Caustic Soda"]
    
    # BOM: 20 RMs with distinct cost weights
    bom_records = []
    for fg in fgs:
        for rm in rms:
            # Critical feedstocks (PTA/MEG) have higher weights
            weight = 0.45 if rm in ["PTA", "MEG"] else 0.02 
            bom_records.append({
                "Finished_Good": fg, "Raw_Material": rm,
                "Base_Cost_MT": np.random.uniform(150, 550), "Usage_Ratio": weight 
            })
    
    # CUSTOMER PERSONAS: Varied Volumes & Contracts to fix "identical bars"
    cust_data = [
        {"Customer": "Nestle", "Vol": 85000, "Type": "Formula", "Elasticity": -0.4},
        {"Customer": "PepsiCo", "Vol": 62000, "Type": "Fixed", "Elasticity": -1.2},
        {"Customer": "Unilever", "Vol": 22000, "Type": "Spot", "Elasticity": -2.5},
        {"Customer": "Coca-Cola", "Vol": 95000, "Type": "Fixed", "Elasticity": -0.8},
        {"Customer": "Danone", "Vol": 41000, "Type": "Formula", "Elasticity": -0.6}
    ]
    
    sales_records = []
    for fg in fgs:
        for c in cust_data:
            sales_records.append({
                "Finished_Good": fg, "Customer": c['Customer'], 
                "Base_Price_MT": np.random.uniform(1480, 1620),
                "Volume_MT": c['Vol'] + np.random.randint(-2000, 2000),
                "Contract_Type": c['Type'], "Elasticity": c['Elasticity']
            })
    return pd.DataFrame(bom_records), pd.DataFrame(sales_records)

bom_df, sales_df = load_indorama_erp_realistic()

# --- 3. PAGE UI ---
st.set_page_config(layout="wide", page_title="Indorama Strategic Twin")
st.title("🛡️  Strategic Digital Twin")

# --- 4. PHASE 1: BASELINE (Current State) ---
st.subheader("📊 Phase 1: Baseline Operational State")

# Calculate baseline landed cost per FG
cost_per_fg = bom_df.groupby('Finished_Good').apply(lambda x: (x['Base_Cost_MT'] * x['Usage_Ratio']).sum() + 90).reset_index()
cost_per_fg.columns = ['Finished_Good', 'Baseline_Landed']

m_base = sales_df.merge(cost_per_fg, on='Finished_Good')
m_base['Baseline_EBITDA'] = (m_base['Base_Price_MT'] - m_base['Baseline_Landed']) * m_base['Volume_MT']

# 6 Baseline KPIs
b1, b2, b3, b4, b5, b6 = st.columns(6)
b1.metric("Baseline EBITDA", f"${m_base['Baseline_EBITDA'].sum()/1e6:.1f}M")
b2.metric("Portfolio Margin %", f"{(m_base['Baseline_EBITDA'].sum() / (m_base['Base_Price_MT']*m_base['Volume_MT']).sum())*100:.1f}%")
b3.metric("Annual Vol (MT)", f"{m_base['Volume_MT'].sum()/1e3:.0f}k")
b4.metric("Avg Price/MT", f"${m_base['Base_Price_MT'].mean():.0f}")
b5.metric("Asset Util %", "94%")
b6.metric("Logistics/MT", "$90")

# Baseline Visualization
bg1, bg2 = st.columns(2)
with bg1:
    st.plotly_chart(px.bar(m_base.groupby('Customer')['Baseline_EBITDA'].sum().reset_index().sort_values('Baseline_EBITDA'), 
                    x='Customer', y='Baseline_EBITDA', title="Current EBITDA Contribution by Account ($)", color_discrete_sequence=['#2E7D32']), use_container_width=True)
with bg2:
    st.plotly_chart(px.pie(m_base, values='Volume_MT', names='Contract_Type', hole=0.4, title="Portfolio Contract Mix"), use_container_width=True)

st.divider()

# --- 5. PHASE 2: AGENTIC SIMULATION ---
st.subheader("🤖 Phase 2: Agentic Market Intelligence Analysis")
if st.button("🚀 Run Analysis: Identify & Apply Market Shocks"):
    with st.status("Agent Scanning Global Markets...", expanded=True) as status:
        st.write("Extracting volatility markers via Tavily & Gemini 2.0 Flash...")
        
        # Agent calculates the impact (Prompting for JSON)
        prompt = """
        Analyze 2026 market risks for Indorama (PET/Fibers). Return JSON ONLY:
        {'crude_oil_price': 98.2, 'gas_price_surge_pct': 24, 'freight_increase_pct': 31, 'tariff_increase_pct': 12, 'risk_summary': 'Geopolitical instability in logistics hubs and energy feedstocks.'}
        """
        response = client_gemini.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        sh = json.loads(response.text.replace('```json', '').replace('```', ''))
        
        # Math Simulation Engine
        oil_m = 1 + ((sh['crude_oil_price'] - 80)/80) * 0.75
        gas_m = 1 + (sh['gas_price_surge_pct']/100)
        fr_m = 1 + (sh['freight_increase_pct']/100)
        tr_m = 1 + (sh['tariff_increase_pct']/100)
        
        m_sim = m_base.copy()
        # Simulated Landed Cost
        m_sim['Sim_Landed'] = (m_sim['Baseline_Landed'] * oil_m * gas_m * tr_m) + (90 * (fr_m - 1))
        
        # EBITDA Impact: Formula contracts recover 60% of the cost increase automatically
        m_sim['Cost_Increase'] = m_sim['Sim_Landed'] - m_sim['Baseline_Landed']
        m_sim['Price_Recovery'] = 0.0
        m_sim.loc[m_sim['Contract_Type'] == 'Formula', 'Price_Recovery'] = m_sim['Cost_Increase'] * 0.60
        
        m_sim['Sim_EBITDA'] = (m_sim['Base_Price_MT'] + m_sim['Price_Recovery'] - m_sim['Sim_Landed']) * m_sim['Volume_MT']
        m_sim['EBITDA_Leakage'] = m_sim['Sim_EBITDA'] - m_sim['Baseline_EBITDA']
        
        st.session_state.m_sim = m_sim
        st.session_state.sh = sh
        status.update(label="Analysis Complete", state="complete")

# --- 6. SIMULATION OUTPUTS (SALES HEAD COMMAND) ---
if 'm_sim' in st.session_state:
    ms = st.session_state.m_sim
    sh = st.session_state.sh
    
    # 🚩 SHOCK PARAMETERS DISPLAY
    st.markdown("#### 🚩 Agentic Findings: Identified Volatility Parameters")
    s1, s2, s3, s4 = st.columns(4)
    s1.error(f"**Crude Oil (Brent):** ${sh['crude_oil_price']}/Bbl")
    s2.error(f"**Natural Gas:** +{sh['gas_price_surge_pct']}%")
    s3.error(f"**Freight:** +{sh['freight_increase_pct']}%")
    s4.error(f"**Tariffs:** +{sh['tariff_increase_pct']}%")
    st.info(f"**Agent Reasoning:** {sh['risk_summary']}")

    # 6 SALES HEAD KPIs (After Shock)
    leak_m = abs(ms['EBITDA_Leakage'].sum()) / 1e6
    hike_req = (abs(ms['EBITDA_Leakage'].sum()) / (ms['Base_Price_MT']*ms['Volume_MT']).sum()) * 100
    vol_risk_kmt = (abs(hike_req * ms['Elasticity'].mean())/100 * ms['Volume_MT'].sum()) / 1e3

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("EBITDA Leakage", f"-${leak_m:.1f}M", delta_color="inverse")
    c2.metric("Rev at Risk (Fixed)", f"${(ms[ms['Contract_Type']=='Fixed']['Volume_MT']*ms['Base_Price_MT']).sum()/1e6:.1f}M")
    c3.metric("Required Hike %", f"{hike_req:.1f}%")
    c4.metric("Demand at Risk", f"{vol_risk_kmt:.1f}k MT")
    c5.metric("New Floor Price", f"${ms['Sim_Landed'].mean():,.0f}")
    c6.metric("Potential Drop %", f"{hike_req * ms['Elasticity'].mean():.1f}%")

    # 6 Graphs
    g1, g2 = st.columns(2)
    with g1:
        # 1. Varied Leakage by Account
        st.plotly_chart(px.bar(ms.groupby('Customer')['EBITDA_Leakage'].sum().abs().reset_index().sort_values('EBITDA_Leakage'), 
                        x='Customer', y='EBITDA_Leakage', title="1. EBITDA Leakage by Account ($M)", color='EBITDA_Leakage', color_continuous_scale='Reds'), use_container_width=True)
        # 2. Landed Cost Migration
        floor = ms.groupby('Finished_Good')[['Baseline_Landed', 'Sim_Landed']].mean().reset_index()
        st.plotly_chart(px.line(floor, x='Finished_Good', y=['Baseline_Landed', 'Sim_Landed'], markers=True, title="2. Landed Cost Floor Migration"), use_container_width=True)
        # 3. Demand Sensitivity
        h_range = np.linspace(0, 30, 10)
        f3 = go.Figure()
        for c in ms['Customer'].unique(): f3.add_trace(go.Scatter(x=h_range, y=h_range * ms[ms['Customer']==c]['Elasticity'].iloc[0], name=c))
        st.plotly_chart(f3.update_layout(title="3. Demand Sensitivity (Vol Loss vs Hike)"), use_container_width=True)
    with g2:
        # 4. Target Price Negotiation
        ms['Target_Price'] = ms['Base_Price_MT'] + (abs(ms['EBITDA_Leakage'])/ms['Volume_MT'])
        st.plotly_chart(px.bar(ms.groupby('Customer')[['Base_Price_MT', 'Target_Price']].mean().reset_index(), x='Customer', y=['Base_Price_MT', 'Target_Price'], barmode='group', title="4. Negotiation Gap: Baseline vs Target"), use_container_width=True)
        # 5. Sunburst Contribution
        st.plotly_chart(px.sunburst(ms, path=['Finished_Good', 'Customer'], values=ms['EBITDA_Leakage'].abs(), title="5. Leakage Contribution by Account"), use_container_width=True)
        # 6. Contract Risk Scatter
        st.plotly_chart(px.scatter(ms, x="Volume_MT", y="EBITDA_Leakage", size=abs(ms['Elasticity']), color="Contract_Type", title="6. Account Risk Distribution (Size = Sensitivity)"), use_container_width=True)

# --- 7. DATA PREVIEW ---
with st.expander("📝 View  Sample Data"):
    st.write("**BOM (20 RMs Sample)**", bom_df.head(20))
    st.write("**Sales Master Sample**", sales_df.head(10))