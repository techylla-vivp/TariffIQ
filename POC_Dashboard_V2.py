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
    # Extended range to mid-2026 for smoother AI forecasting
    months = pd.date_range(start="2025-01-01", end="2026-06-01", freq='ME') 
    data = []
    hierarchy = {
        "Therapeutic Area: Oncology": {"Small Molecules": ["API Intermediates", "Reagents"], "Biologics": ["Cell Culture Media"], "Target_Rate": 0.90},
        "Therapeutic Area: Respiratory": {"Inhaler Components": ["Valves", "Actuators"], "API": ["Active Ingredients"], "Target_Rate": 0.75},
        "Therapeutic Area: Immunology": {"Antibodies": ["Monoclonal Antibodies"], "Excipients": ["Specialty Sugars"], "Target_Rate": 0.85},
        "Animal Health": {"Vaccines": ["Adjuvants"], "Parasiticides": ["Raw Materials"], "Target_Rate": 0.65}
    }
    countries = ["Germany", "USA", "China", "India", "Austria", "Japan"]
    
    total_steps = len(months)
    for i, m in enumerate(months):
        # FIX: Linear growth (from 8.0% to 10.5%) to prevent the Jan 2026 vertical spike
        current_rate = 0.08 + (i * (0.025 / total_steps))
        
        for vc, config in hierarchy.items():
            target_rate = config["Target_Rate"]
            for cat, prods in {k: v for k, v in config.items() if k != "Target_Rate"}.items():
                for prod in prods:
                    proc_val = np.random.uniform(750000, 850000)
                    gross = proc_val * current_rate
                    realized = gross * np.random.uniform(0.45, 0.55) 
                    net = gross - realized
                    potential_savings = gross * target_rate
                    unrealized = max(0, potential_savings - realized)
                    
                    data.append({
                        "Date": m, "Year": str(m.year), "Month_Year": m.strftime("%b %Y"),
                        "Value_Chain": vc, "Category": cat, "Product": prod, "Country": np.random.choice(countries),
                        "Procurement_Value": proc_val, "Gross_Impact": gross,
                        "Realized_Mitigation": realized, "Net_Impact": net,
                        "Unrealized_Mitigation": unrealized,
                        "Lead_Time": np.random.randint(30, 60)
                    })
    return pd.DataFrame(data)

# --- 2. CSS STYLING (PRESERVED) ---
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

# --- 3. HEADER & SIDEBAR ---
st.title("🛡️ Global Trade & Tariff Intelligence")
st.markdown("##### *Trade Intelligence & Procurement Strategy Suite*")

with st.sidebar:
    st.title("🔍 Portfolio Filters")
    sel_year = st.multiselect("Reporting Year", ["2025", "2026"], default=["2025", "2026"])
    sel_vc = st.multiselect("Therapeutic Area", df["Value_Chain"].unique(), default=df["Value_Chain"].unique())
    sub_df = df[df["Value_Chain"].isin(sel_vc)]
    sel_cat = st.multiselect("Material Category", sub_df["Category"].unique(), default=sub_df["Category"].unique())
    f_df = df[(df["Year"].isin(sel_year)) & (df["Value_Chain"].isin(sel_vc)) & (df["Category"].isin(sel_cat))]

# --- 4. TOP KPI ROW ---
metrics = [
    ("Procurement Spend", f_df["Procurement_Value"].sum(), "Total purchase value of materials.", "#6366F1"),
    ("Gross Impact", f_df["Gross_Impact"].sum(), "Total theoretical duty liability.", "#004A7C"),
    ("Realized Savings", f_df["Realized_Mitigation"].sum(), "Actual duty avoided.", "#10B981"),
    ("Net Duty Paid", f_df["Net_Impact"].sum(), "Actual cash outflow.", "#EF4444"),
    ("Unrealized Leakage", f_df["Unrealized_Mitigation"].sum(), "Fixable savings potential missed.", "#F59E0B")
]

kpi_cols = st.columns(5)
for i, (label, val, explanation, color) in enumerate(metrics):
    with kpi_cols[i]:
        st.markdown(f'<div class="kpi-card" style="border-top-color: {color}"><div class="kpi-label">{label}</div><div class="kpi-value">${val/1e6:.2f}M</div></div>', unsafe_allow_html=True)
        st.button("ⓘ Info", key=f"k_btn_{i}", help=f"**{label}**\n\n{explanation}")

def draw_graph_card(title, info, fig):
    st.markdown(f'''<div class="graph-header"><p class="graph-title">{title}</p></div>''', unsafe_allow_html=True)
    st.button("ℹ️ Insights", key=f"btn_{title}", help=info)
    st.plotly_chart(fig, use_container_width=True)

# --- 5. VISUALIZATIONS (LOCKED 2-COLUMN GRID) ---

st.markdown('<div class="section-title">I. Strategic Performance & Geographic Risk</div>', unsafe_allow_html=True)
r1_c1, r1_c2 = st.columns(2)
with r1_c1:
    g1_df = f_df.groupby("Date").agg({"Procurement_Value":"sum","Gross_Impact":"sum","Realized_Mitigation":"sum","Net_Impact":"sum","Unrealized_Mitigation":"sum"}).reset_index()
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=g1_df['Date'], y=g1_df['Procurement_Value'], name='Spend', marker_color='#E2E8F0', yaxis='y2', opacity=0.4))
    fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Gross_Impact'], name='Gross Impact', line=dict(color='#004A7C', width=3)))
    fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Net_Impact'], name='Net Duty (Actual)', line=dict(color='#EF4444', width=4)))
    fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Unrealized_Mitigation'], name='Leakage', line=dict(color='#F59E0B', width=2, dash='dash')))
    fig1.update_layout(height=400, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white", yaxis2=dict(overlaying="y", side="right", showgrid=False), legend=dict(orientation="h", y=1.2))
    draw_graph_card("G1: Strategic Impact Trend", "Tracking the gap between Gross liability and Net cost.", fig1)
with r1_c2:
    y_df = (f_df.groupby("Month_Year")["Realized_Mitigation"].sum() / f_df.groupby("Month_Year")["Gross_Impact"].sum() * 100).reset_index()
    y_df['Date_Sort'] = pd.to_datetime(y_df['Month_Year'])
    y_df = y_df.sort_values('Date_Sort')
    fig2 = px.area(y_df, x="Month_Year", y=0, color_discrete_sequence=['#10B981'], height=400)
    fig2.update_layout(yaxis_title="Efficiency %", margin=dict(l=0,r=0,t=0,b=0))
    draw_graph_card("G2: Efficiency Yield %", "Percentage of Gross Impact successfully mitigated.", fig2)

st.markdown('<div class="section-title">II. Portfolio & Leakage Analysis</div>', unsafe_allow_html=True)
r2_c1, r2_c2 = st.columns(2)
with r2_c1:
    fig3 = px.imshow(f_df.pivot_table(index='Country', columns='Value_Chain', values='Net_Impact', aggfunc='sum'), color_continuous_scale='Reds', height=400)
    draw_graph_card("G3: Geographic Heatmap", "Identifies Country/Value Chain intersections with highest cash outflow.", fig3)
with r2_c2:
    pareto = f_df.groupby("Product")["Unrealized_Mitigation"].sum().sort_values(ascending=True).reset_index()
    fig4 = px.bar(pareto, x="Unrealized_Mitigation", y="Product", orientation='h', color_discrete_sequence=['#F59E0B'], height=400)
    draw_graph_card("G4: Product Leakage Pareto", "Top products contributing to missed savings opportunities.", fig4)

r3_c1, r3_c2 = st.columns(2)
with r3_c1:
    fig5 = px.box(f_df, x="Year", y="Net_Impact", color="Year", height=400)
    draw_graph_card("G5: Cost Stability Analysis", "Volatility of Net Duty costs per year.", fig5)
with r3_c2:
    vc_df = f_df.groupby("Value_Chain")[["Gross_Impact", "Net_Impact"]].sum().reset_index()
    fig6 = px.bar(vc_df, x="Value_Chain", y=["Gross_Impact", "Net_Impact"], barmode="group", height=400)
    draw_graph_card("G6: VC Performance", "Gross vs Net Impact comparison across business units.", fig6)

st.markdown('<div class="section-title">III. Logistics & Efficiency Insights</div>', unsafe_allow_html=True)
r4_c1, r4_c2 = st.columns(2)
with r4_c1:
    fig7 = px.line(g1_df, x="Date", y=["Realized_Mitigation", "Unrealized_Mitigation"], height=400)
    draw_graph_card("G7: Savings vs Leakage", "Running trend of realized value vs addressable loss.", fig7)
with r4_c2:
    fig8 = px.scatter(f_df, x="Lead_Time", y="Net_Impact", color="Country", height=400)
    draw_graph_card("G8: Lead Time vs Duty Correlation", "Correlation between supply chain delays and duty costs.", fig8)

r5_c1, r5_c2 = st.columns(2)
with r5_c1:
    country_leak = (f_df.groupby("Country")["Unrealized_Mitigation"].sum() / f_df.groupby("Country")["Gross_Impact"].sum() * 100).reset_index()
    fig9 = px.bar(country_leak, x="Country", y=0, color_discrete_sequence=['#8B5CF6'], height=400)
    draw_graph_card("G9: Country Leakage %", "Proportion of missed savings per origin country.", fig9)
with r5_c2:
    cat_df = f_df.groupby("Category").agg({"Procurement_Value":"sum", "Realized_Mitigation":"sum", "Gross_Impact":"sum"}).reset_index()
    cat_df['Yield'] = (cat_df['Realized_Mitigation'] / cat_df['Gross_Impact']) * 100
    fig10 = px.scatter(cat_df, x="Category", y="Yield", size="Procurement_Value", color="Category", height=400)
    draw_graph_card("G10: Category Yield Matrix", "Bubble size = Spend; Y-axis = Mitigation Efficiency.", fig10)

st.markdown('<div class="section-title">IV. AI Predictive Risk Horizon</div>', unsafe_allow_html=True)
r6_c1, r6_c2 = st.columns(2)
with r6_c1:
    trend_data = f_df.groupby("Date")["Net_Impact"].sum().reset_index()
    trend_data['Date_Ordinal'] = trend_data['Date'].apply(lambda x: x.toordinal())
    model = LinearRegression().fit(trend_data[['Date_Ordinal']], trend_data['Net_Impact'])
    future_dates = pd.date_range(start="2026-07-01", periods=6, freq='ME')
    forecast_df = pd.DataFrame({'Date': future_dates, 'Net_Impact': model.predict(np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)), 'Type': 'AI Forecast'})
    trend_data['Type'] = 'Actual'
    fig11 = px.line(pd.concat([trend_data, forecast_df]), x="Date", y="Net_Impact", color="Type", line_dash="Type", height=400)
    draw_graph_card("G11: ML Net Impact Forecast", "6-month prediction of duty cash outflow.", fig11)
with r6_c2:
    sim_data = np.random.normal(f_df["Unrealized_Mitigation"].mean(), f_df["Unrealized_Mitigation"].std(), 1000)
    fig12 = px.histogram(sim_data, nbins=40, color_discrete_sequence=['#004A7C'], height=400)
    draw_graph_card("G12: Value at Risk (Monte Carlo)", "Simulated risk distribution for potential leakage.", fig12)

# --- 6. AUDIT TABLE ---
st.markdown('<div class="section-title">V. Transactional Audit Ledger</div>', unsafe_allow_html=True)

st.dataframe(f_df.sort_values("Date", ascending=False), use_container_width=True)
