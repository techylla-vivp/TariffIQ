import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import datetime

# --- 1. SET PAGE CONFIG & DATA GENERATION ---
st.set_page_config(layout="wide", page_title="Sourcing & Tariff Impact Dashboard")

@st.cache_data
def get_chemical_data():
    months = pd.date_range(start="2025-01-01", end="2026-02-01", freq='ME') 
    data = []
    hierarchy = {
        "Water Treatment": {"Polymers": ["Polyacrylamide", "DADMAC"], "Coagulants": ["Alum", "PAC"]},
        "Pulp & Paper": {"Defoamers": ["Silicone Oil"], "Biocides": ["Glutaraldehyde"]},
        "Mining Solutions": {"Collectors": ["Xanthates"], "Frothers": ["MIBC"]},
        "Consumer Specialties": {"Surfactants": ["SLES", "LABSA"]}
    }
    countries = ["China", "India", "Germany", "Mexico", "USA", "South Korea"]
    for m in months:
        for vc, cats in hierarchy.items():
            for cat, prods in cats.items():
                for prod in prods:
                    proc_val = np.random.uniform(300000, 900000)
                    base_rate = 0.22 if m.year == 2026 else 0.12
                    gross = proc_val * base_rate
                    realized = gross * np.random.uniform(0.4, 0.65)
                    net = gross - realized
                    data.append({
                        "Date": m, "Year": str(m.year), "Month_Year": m.strftime("%b %Y"),
                        "Value_Chain": vc, "Category": cat, "Product": prod, "Country": np.random.choice(countries),
                        "Procurement_Value": proc_val, "Gross_Impact": gross,
                        "Realized_Mitigation": realized, "Net_Impact": net,
                        "Mitigation_Forecast": realized * 1.15, "Unmitigated_Exposure": net,
                        "Compliance_Score": np.random.uniform(60, 95), "Lead_Time": np.random.randint(15, 75)
                    })
    return pd.DataFrame(data)

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    [data-testid="column"] { display: flex; flex-direction: column; }
    .kpi-card {
        background-color: #ffffff; padding: 20px 10px; border-radius: 10px;
        border-top: 6px solid #004A7C; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        text-align: center; width: 100%; min-height: 140px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    .kpi-label { font-size: 13px; color: #475569; font-weight: 700; text-transform: uppercase; margin-bottom: 10px; }
    .kpi-value { font-size: 26px; color: #1e293b; font-weight: 800; }
    .section-title { font-size: 22px; font-weight: bold; color: #004A7C; border-bottom: 2px solid #e2e8f0; margin: 35px 0 15px 0; }
    </style>
    """, unsafe_allow_html=True)

df = get_chemical_data()

# --- 3. HEADER & SIDEBAR ---
st.title("🛡️ Sourcing & Tariff Impact Dashboard")
st.markdown("##### *Trade Intelligence & Procurement Strategy Suite *")
st.sidebar.caption(f"Last Refresh: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")

with st.sidebar:
    st.title("🔍 Strategic Filters")
    sel_year = st.multiselect("Year", ["2025", "2026"], default=["2025", "2026"])
    sel_vc = st.multiselect("Value Chain", df["Value_Chain"].unique(), default=df["Value_Chain"].unique())
    sub_df = df[df["Value_Chain"].isin(sel_vc)]
    sel_cat = st.multiselect("Category", sub_df["Category"].unique(), default=sub_df["Category"].unique())
    f_df = df[(df["Year"].isin(sel_year)) & (df["Value_Chain"].isin(sel_vc)) & (df["Category"].isin(sel_cat))]

# --- 4. TOP KPI ROW ---
metrics = [
    ("Procurement Value", f_df["Procurement_Value"].sum(), "$\sum Spend$", "#6366F1"),
    ("Gross Impact", f_df["Gross_Impact"].sum(), "$Value \\times Rate$", "#004A7C"),
    ("Realized Mitigation", f_df["Realized_Mitigation"].sum(), "$Gross - Paid$", "#10B981"),
    ("Net Impact", f_df["Net_Impact"].sum(), "$Actual Cost$", "#EF4444"),
    ("Mitigation Forecast", f_df["Mitigation_Forecast"].sum(), "$Next Project Savings$", "#8B5CF6"),
    ("Unmitigated Exposure", f_df["Unmitigated_Exposure"].sum(), "$Opportunity$", "#F59E0B")
]
kpi_cols = st.columns(6)
for i, (label, val, formula, color) in enumerate(metrics):
    with kpi_cols[i]:
        st.markdown(f'<div class="kpi-card" style="border-top-color: {color}"><div class="kpi-label">{label}</div><div class="kpi-value">{val/1e6:.2f}M</div></div>', unsafe_allow_html=True)
        st.button("ⓘ", key=f"k_btn_{i}", help=f"**{label}**\n\n{formula}")

# --- 5. G1: BALANCED COMBO TREND (DUAL AXIS) ---
st.markdown('<div class="section-title">I. Strategic Performance Horizon</div>', unsafe_allow_html=True)
g1_df = f_df.groupby("Date").agg({
    "Procurement_Value": "sum", "Gross_Impact": "sum", "Realized_Mitigation": "sum",
    "Net_Impact": "sum", "Mitigation_Forecast": "sum", "Unmitigated_Exposure": "sum"
}).reset_index()

fig1 = go.Figure()

# 1. Bar Graph for Spend (Right Axis)
fig1.add_trace(go.Bar(
    x=g1_df['Date'], y=g1_df['Procurement_Value'], 
    name='Procurement Spend', marker_color='#E2E8F0', # Neutral grey-blue to not distract
    yaxis='y2', opacity=0.4
))

# 2. Solid Lines for Actuals (Left Axis)
fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Gross_Impact'], name='Gross Impact', line=dict(color='#004A7C', width=3)))
fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Realized_Mitigation'], name='Realized Mitigation', line=dict(color='#10B981', width=3)))
fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Net_Impact'], name='Net Impact (Actual Cost)', line=dict(color='#EF4444', width=4)))

# 3. Dashed Lines for Future/Risk (Left Axis)
fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Mitigation_Forecast'], name='Savings Forecast', line=dict(color='#8B5CF6', width=2, dash='dot')))
fig1.add_trace(go.Scatter(x=g1_df['Date'], y=g1_df['Unmitigated_Exposure'], name='Residual Risk', line=dict(color='#F59E0B', width=2, dash='dash')))

# 4. Layout with Dual Axis Logic
fig1.update_layout(
    height=550,
    xaxis_title="Timeline",
    yaxis=dict(title="Tariff & Impact ($)", side="left"),
    yaxis2=dict(title="Total Procurement Spend ($)", side="right", overlaying="y", showgrid=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(fig1, use_container_width=True)
# --- 6. G2 - G10 (2 PER ROW) ---
st.markdown('<div class="section-title">II. Tactical & Geographic Analytics</div>', unsafe_allow_html=True)
c2, c3 = st.columns(2)
with c2:
    st.subheader("G2: Efficiency Yield %")
    y_df = (f_df.groupby("Month_Year")["Realized_Mitigation"].sum() / f_df.groupby("Month_Year")["Gross_Impact"].sum() * 100).reset_index()
    st.plotly_chart(px.area(y_df, x="Month_Year", y=0, color_discrete_sequence=['#10B981']), use_container_width=True)
with c3:
    st.subheader("G3: Geographic Risk Heatmap")
    st.plotly_chart(px.imshow(f_df.pivot_table(index='Country', columns='Value_Chain', values='Net_Impact', aggfunc='sum'), color_continuous_scale='Reds'), use_container_width=True)

c4, c5 = st.columns(2)
with c4:
    st.subheader("G4: Product Exposure Pareto")
    st.plotly_chart(px.bar(f_df.groupby("Product")["Unmitigated_Exposure"].sum().sort_values().reset_index(), x="Unmitigated_Exposure", y="Product", orientation='h'), use_container_width=True)
with c5:
    st.subheader("G5: Impact Stability")
    st.plotly_chart(px.box(f_df, x="Year", y="Net_Impact", color="Year"), use_container_width=True)

c6, c7 = st.columns(2)
with c6:
    st.subheader("G6: Compliance ROI Scatter")
    st.plotly_chart(px.scatter(f_df, x="Compliance_Score", y="Net_Impact", color="Category", size="Procurement_Value"), use_container_width=True)
with c7:
    st.subheader("G7: Cumulative Gap Burn")
    f_df['Cum_Gap'] = f_df.sort_values('Date')['Unmitigated_Exposure'].cumsum()
    st.plotly_chart(px.area(f_df, x="Date", y="Cum_Gap", color_discrete_sequence=['#EF4444']), use_container_width=True)

c8, c9 = st.columns(2)
with c8:
    st.subheader("G8: Lead Time Correlation")
    st.plotly_chart(px.density_heatmap(f_df, x="Lead_Time", y="Realized_Mitigation", color_continuous_scale='Viridis'), use_container_width=True)
with c9:
    st.subheader("G9: Spend vs Risk Bubble")
    bubble_df = f_df.groupby("Category").agg({"Procurement_Value":"sum", "Net_Impact":"sum"}).reset_index()
    st.plotly_chart(px.scatter(bubble_df, x="Procurement_Value", y="Net_Impact", size="Net_Impact", color="Category", text="Category"), use_container_width=True)

c10, _ = st.columns(2)
with c10:
    st.subheader("G10: Monthly Seasonality Analysis")
    st.plotly_chart(px.line(f_df.groupby("Month_Year")["Unmitigated_Exposure"].sum().reset_index(), x="Month_Year", y="Unmitigated_Exposure", markers=True), use_container_width=True)

# --- 7. AUDIT TABLE ---
st.markdown('<div class="section-title">III. Transactional Audit Ledger</div>', unsafe_allow_html=True)
st.dataframe(f_df.sort_values("Date", ascending=False), use_container_width=True)

# --- 8. AI PREDICTIVE INTELLIGENCE ---
st.markdown('<div class="section-title">IV. AI Predictive Intelligence</div>', unsafe_allow_html=True)
pa1, pa2 = st.columns(2)

with pa1:
    st.subheader("G11: ML Exposure Forecast (6-Mo)")
    trend_data = f_df.groupby("Date")["Net_Impact"].sum().reset_index()
    trend_data['Date_Ordinal'] = trend_data['Date'].apply(lambda x: x.toordinal())
    model = LinearRegression().fit(trend_data[['Date_Ordinal']], trend_data['Net_Impact'])
    future_dates = pd.date_range(start="2026-03-01", periods=6, freq='ME')
    future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
    forecast_df = pd.DataFrame({'Date': future_dates, 'Net_Impact': model.predict(future_ordinals), 'Type': 'AI Prediction'})
    trend_data['Type'] = 'Actual'
    st.plotly_chart(px.line(pd.concat([trend_data, forecast_df]), x="Date", y="Net_Impact", color="Type", line_dash="Type"), use_container_width=True)

with pa2:
    st.subheader("G12: Monte Carlo Risk Distribution")
    sim_data = np.random.normal(f_df["Unmitigated_Exposure"].mean(), f_df["Unmitigated_Exposure"].std(), 1000)
    var_95 = np.percentile(sim_data, 95)
    st.info(f"**95% Confidence Risk Level:** ${var_95/1e6:.2f}M")
    fig12 = px.histogram(sim_data, nbins=50, color_discrete_sequence=['#8B5CF6'], labels={'value': 'Predicted Unmitigated Exposure ($)'})
    fig12.add_vline(x=var_95, line_dash="dash", line_color="red", annotation_text=f"95% Threshold: ${var_95/1e6:.1f}M")
    st.plotly_chart(fig12, use_container_width=True)