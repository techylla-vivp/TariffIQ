import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import datetime

# --- 1. SET PAGE CONFIG & DATA GENERATION ---
st.set_page_config(layout="wide", page_title="Global Trade Intelligence")

@st.cache_data
def get_pharma_trade_data():
    months = pd.date_range(start="2025-01-01", end="2026-06-01", freq='ME') 
    data = []
    hierarchy = {
        "Oncology": {"Small Molecules": ["API Intermediates", "Reagents"], "Biologics": ["Cell Culture Media"], "Target_Rate": 0.90},
        "Respiratory": {"Inhaler Components": ["Valves", "Actuators"], "API": ["Active Ingredients"], "Target_Rate": 0.75},
        "Immunology": {"Antibodies": ["Monoclonal Antibodies"], "Excipients": ["Specialty Sugars"], "Target_Rate": 0.85},
        "Animal Health": {"Vaccines": ["Adjuvants"], "Parasiticides": ["Raw Materials"], "Target_Rate": 0.65}
    }
    countries = ["Germany", "USA", "China", "India", "Austria", "Japan"]
    
    total_steps = len(months)
    for i, m in enumerate(months):
        current_rate = 0.08 + (i * (0.025 / total_steps))
        
        for ta, config in hierarchy.items():
            target_rate = config["Target_Rate"]
            for cat, prods in {k: v for k, v in config.items() if k != "Target_Rate"}.items():
                for prod in prods:
                    # Scaling Factor: 12x Inflation
                    scale = 12
                    proc_val = np.random.uniform(750000, 850000) * scale
                    gross = proc_val * current_rate
                    realized = gross * np.random.uniform(0.45, 0.55) 
                    net = gross - realized
                    potential_total = gross * target_rate
                    recovery = max(0, potential_total - realized)
                    
                    data.append({
                        "Date": m, "Year": str(m.year), "Month_Year": m.strftime("%b %Y"),
                        "Therapeutic_Area": ta, "Category": cat, "Product": prod, "Country": np.random.choice(countries),
                        "Procurement_Value": proc_val, 
                        "Gross_Exposure": gross,
                        "Mitigation_Forecast": realized, 
                        "Net_Exposure": net,
                        "Potential_Recovery": recovery
                    })
    return pd.DataFrame(data)

# --- 2. DYNAMIC STRATEGY ENGINE (ENFORCED) ---
def get_realistic_levers(cat, country):
    """Calculates mitigation levers based on Product Profile and Trade Corridors"""
    if cat in ["API", "Small Molecules", "Raw Materials"]:
        fta, susp, reclass = 0.25, 0.55, 0.20
        note = "High eligibility for Duty Suspensions (Chapter 99) for raw inputs."
    elif cat in ["Inhaler Components", "Biologics"]:
        fta, susp, reclass = 0.60, 0.15, 0.25
        note = "Priority: FTA qualification. Validate regional value content (RVC)."
    else:
        fta, susp, reclass = 0.35, 0.30, 0.35
        note = "General Audit: Re-classify and check for multi-corridor FTA eligibility."
    
    # Corridor specific logic (e.g., China/India have complex FTA landscape)
    if country in ["China", "India"] and fta > 0.4:
        fta -= 0.20
        susp += 0.20
        
    return {"FTA": fta, "Suspension": susp, "Reclass": reclass, "Note": note}

# --- 3. CSS STYLING ---
st.markdown("""
    <style>
    .kpi-card {
        background-color: #ffffff; padding: 20px 10px; border-radius: 10px;
        border-top: 6px solid #004A7C; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        text-align: center; width: 100%; min-height: 140px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    .kpi-label { font-size: 13px; color: #475569; font-weight: 700; text-transform: uppercase; margin-bottom: 10px; }
    .kpi-value { font-size: 26px; color: #1e293b; font-weight: 800; }
    .section-title { font-size: 22px; font-weight: bold; color: #004A7C; border-bottom: 2px solid #e2e8f0; margin: 35px 0 15px 0; }
    .graph-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px; background: #f8fafc; padding: 8px 12px; border-radius: 5px; border: 1px solid #e2e8f0; }
    .graph-title { font-size: 16px; font-weight: 600; color: #1e293b; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

df = get_pharma_trade_data()

# --- 4. HEADER & SIDEBAR ---
st.title("🛡️ Global Trade & Tariff Intelligence")
st.markdown("##### *Trade Intelligence & Procurement Strategy Suite*")

with st.sidebar:
    st.title("🔍 Portfolio Filters")
    sel_year = st.multiselect("Reporting Year", ["2025", "2026"], default=["2025", "2026"])
    sel_ta = st.multiselect("Therapeutic Area", df["Therapeutic_Area"].unique(), default=df["Therapeutic_Area"].unique())
    sub_df = df[df["Therapeutic_Area"].isin(sel_ta)]
    sel_cat = st.multiselect("Material Category", sub_df["Category"].unique(), default=sub_df["Category"].unique())
    f_df = df[(df["Year"].isin(sel_year)) & (df["Therapeutic_Area"].isin(sel_ta)) & (df["Category"].isin(sel_cat))]

# --- 5. TOP KPI ROW ---
metrics = [
    ("Gross Exposure", f_df["Gross_Exposure"].sum(), "Total theoretical duty liability .", "#004A7C"),
    ("Mitigation Forecast", f_df["Mitigation_Forecast"].sum(), "Projected duty avoided through existing programs.", "#10B981"),
    ("Net Exposure", f_df["Net_Exposure"].sum(), "Actual cash outflow (Duty Paid).", "#EF4444"),
    ("Potential Recovery", f_df["Potential_Recovery"].sum(), "Addressable savings potential remaining.", "#F59E0B")
]

kpi_cols = st.columns(4)
for i, (label, val, explanation, color) in enumerate(metrics):
    with kpi_cols[i]:
        st.markdown(f'<div class="kpi-card" style="border-top-color: {color}"><div class="kpi-label">{label}</div><div class="kpi-value">${val/1e6:.2f}M</div></div>', unsafe_allow_html=True)
        st.button("ⓘ Info", key=f"k_btn_{i}", help=f"**{label}**\n\n{explanation}")

def draw_graph_card(title, info, fig):
    st.markdown(f'''<div class="graph-header"><p class="graph-title">{title}</p></div>''', unsafe_allow_html=True)
    st.button("ℹ️ Insights", key=f"btn_{title}", help=info)
    st.plotly_chart(fig, use_container_width=True)

# --- 6. VISUALIZATIONS ---

st.markdown('<div class="section-title">I. Strategic Performance & Geographic Risk</div>', unsafe_allow_html=True)
r1_c1, r1_c2 = st.columns(2)
with r1_c1:
    g1_df = f_df.groupby("Date").agg({"Gross_Exposure":"sum","Mitigation_Forecast":"sum","Net_Exposure":"sum","Potential_Recovery":"sum"}).reset_index()
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Gross_Exposure'], name='Gross Exposure', line=dict(color='#004A7C', width=2)))
    fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Net_Exposure'], name='Net Exposure', line=dict(color='#EF4444', width=4)))
    fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Potential_Recovery'], name='Potential Recovery', line=dict(color='#F59E0B', width=2, dash='dash')))
    fig1.add_vline(x=datetime.date(2026, 2, 23), line_width=2, line_dash="dash", line_color="gray")
    fig1.update_layout(height=400, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white", legend=dict(orientation="h", y=1.2))
    draw_graph_card("G1: Strategic Exposure Trend", "Trend of Gross, Net, and Potential Recovery. Dotted line = Today.", fig1)
with r1_c2:
    y_df = (f_df.groupby("Month_Year")["Mitigation_Forecast"].sum() / f_df.groupby("Month_Year")["Gross_Exposure"].sum() * 100).reset_index()
    y_df['Date_Sort'] = pd.to_datetime(y_df['Month_Year'])
    y_df = y_df.sort_values('Date_Sort')
    fig2 = px.area(y_df, x="Month_Year", y=0, color_discrete_sequence=['#10B981'], height=400)
    draw_graph_card("G2: Mitigation Efficiency Yield %", "Yield effectiveness: Percentage of Gross successfully mitigated.", fig2)

st.markdown('<div class="section-title">II. Portfolio & Potential Recovery Analysis</div>', unsafe_allow_html=True)
r2_c1, r2_c2 = st.columns(2)
with r2_c1:
    fig3 = px.imshow(f_df.pivot_table(index='Country', columns='Therapeutic_Area', values='Net_Exposure', aggfunc='sum'), color_continuous_scale='Reds', height=400)
    draw_graph_card("G3: Geographic Exposure Heatmap", "Net Exposure concentration by Therapeutic Area and Country.", fig3)
with r2_c2:
    pareto = f_df.groupby("Product")["Potential_Recovery"].sum().sort_values(ascending=True).reset_index()
    fig4 = px.bar(pareto, x="Potential_Recovery", y="Product", orientation='h', color_discrete_sequence=['#F59E0B'], height=400)
    draw_graph_card("G4: Potential Recovery Pareto", "Identifying products with the highest addressable recovery opportunities.", fig4)

# --- SECTION III: STRATEGY DRILL-DOWN (ENFORCED & INTERACTIVE) ---
st.markdown('<div class="section-title">III. Strategy Drill-Down: Actionable Recovery Levers</div>', unsafe_allow_html=True)
# Target products with highest Potential Recovery
target_products_df = f_df.groupby(["Product", "Category", "Country"]).agg({"Potential_Recovery":"sum"}).reset_index().sort_values("Potential_Recovery", ascending=False)
selected_p = st.selectbox("🎯 Select a product from G4 to define the execution path:", target_products_df["Product"])

selected_row = target_products_df[target_products_df["Product"] == selected_p].iloc[0]
strat = get_realistic_levers(selected_row["Category"], selected_row["Country"])

col_a, col_b = st.columns([1, 2])
with col_a:
    st.write(f"### Product: {selected_p}")
    st.metric("Addressable Recovery", f"${selected_row['Potential_Recovery']/1e3:.1f}K")
    st.info(f"**Action Recommendation:** {strat['Note']}")
    st.markdown(f"""
    **Trade Parameters:**
    - **Category:** {selected_row['Category']}
    - **Origin:** {selected_row['Country']}
    """)
with col_b:
    fig_pie = px.pie(names=["FTA Utilization", "Tariff Suspension", "HS Reclassification"], 
                     values=[strat['FTA'], strat['Suspension'], strat['Reclass']], 
                     hole=0.4, height=320, color_discrete_sequence=px.colors.qualitative.Prism)
    fig_pie.update_layout(title=f"Lever Allocation for {selected_p}")
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown('<div class="section-title">IV. AI Predictive Risk Horizon</div>', unsafe_allow_html=True)
r4_c1, r4_c2 = st.columns(2)
with r4_c1:
    trend_data = f_df.groupby("Date")["Net_Exposure"].sum().reset_index()
    trend_data['Date_Ordinal'] = trend_data['Date'].apply(lambda x: x.toordinal())
    model = LinearRegression().fit(trend_data[['Date_Ordinal']], trend_data['Net_Exposure'])
    future_dates = pd.date_range(start="2026-07-01", periods=6, freq='ME')
    forecast_df = pd.DataFrame({'Date': future_dates, 'Net_Exposure': model.predict(np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)), 'Type': 'AI Forecast'})
    trend_data['Type'] = 'Actual'
    fig11 = px.line(pd.concat([trend_data, forecast_df]), x="Date", y="Net_Exposure", color="Type", line_dash="Type", height=400)
    draw_graph_card("G7: ML Net Exposure Forecast", "AI-driven 6-month prediction of duty cash outflow.", fig11)
#with r4_c2:
#    sim_data = np.random.normal(f_df["Potential_Recovery"].mean(), f_df["Potential_Recovery"].std(), 1000)
#    fig12 = px.histogram(sim_data, nbins=40, color_discrete_sequence=['#004A7C'], height=400)
#    draw_graph_card("G8: Value at Risk (Monte Carlo)", "Simulated distribution of Potential Recovery at risk.", fig12)

# --- 7. AUDIT TABLE ---
st.markdown('<div class="section-title">V. Transactional Audit Ledger</div>', unsafe_allow_html=True)
st.dataframe(f_df.sort_values("Date", ascending=False), use_container_width=True)


