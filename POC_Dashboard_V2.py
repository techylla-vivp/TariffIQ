import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime

# --- 1. SET PAGE CONFIG & DATA GENERATION ---
st.set_page_config(layout="wide", page_title="Global Trade Intelligence")

@st.cache_data
def get_pharma_trade_data():
    months = pd.date_range(start="2025-01-01", end="2026-12-01", freq='ME') 
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
                    scale = 12
                    proc_val = np.random.uniform(750000, 850000) * scale
                    gross = proc_val * current_rate
                    realized = gross * np.random.uniform(0.45, 0.55) 
                    net = gross - realized
                    potential_total = gross * target_rate
                    recovery = max(0, potential_total - realized)
                    
                    data.append({
                        "Date": m, "Year": str(m.year), "Month Year": m.strftime("%b %Y"),
                        "Therapeutic Area": ta, "Category": cat, "Product": prod, "Country": np.random.choice(countries),
                        "Procurement Value": proc_val, 
                        "Gross Exposure": gross,
                        "Mitigation Forecast": realized, 
                        "Net Exposure": net,
                        "Potential Recovery": recovery
                    })
    return pd.DataFrame(data)

# --- 2. DYNAMIC STRATEGY ENGINE ---
def get_realistic_levers(cat, country):
    if cat in ["API", "Small Molecules", "Raw Materials"]:
        fta, susp, reclass = 0.25, 0.55, 0.20
        note = "High eligibility for Duty Suspensions (Chapter 99) for raw inputs."
    elif cat in ["Inhaler Components", "Biologics"]:
        fta, susp, reclass = 0.60, 0.15, 0.25
        note = "Priority: FTA qualification. Validate regional value content (RVC)."
    else:
        fta, susp, reclass = 0.35, 0.30, 0.35
        note = "General Audit: Re-classify and check for multi-corridor FTA eligibility."
    
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
    sel_year = st.multiselect("Reporting Year", ["2025", "2026"], default=["2026"])
    sel_ta = st.multiselect("Therapeutic Area", df["Therapeutic Area"].unique(), default=df["Therapeutic Area"].unique())
    sub_df = df[df["Therapeutic Area"].isin(sel_ta)]
    sel_cat = st.multiselect("Material Category", sub_df["Category"].unique(), default=sub_df["Category"].unique())
    f_df = df[(df["Year"].isin(sel_year)) & (df["Therapeutic Area"].isin(sel_ta)) & (df["Category"].isin(sel_cat))]

# --- 5. TOP KPI ROW ---
metrics = [
    ("Gross Exposure", f_df["Gross Exposure"].sum(), "Total theoretical duty liability.", "#004A7C"),
    ("Mitigation Forecast", f_df["Mitigation Forecast"].sum(), "Projected duty avoided through existing programs.", "#10B981"),
    ("Net Exposure", f_df["Net Exposure"].sum(), "Actual cash outflow (Duty Paid).", "#EF4444"),
    ("Potential Recovery", f_df["Potential Recovery"].sum(), "Addressable savings potential remaining.", "#F59E0B")
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

st.markdown('<div class="section-title">I. 2026 Strategic Performance Outlook</div>', unsafe_allow_html=True)
# Expanding G1 to full width for better trend visibility
g1_df_2026 = f_df[f_df["Year"] == "2026"].groupby("Date").agg({
    "Gross Exposure":"sum",
    "Net Exposure":"sum",
    "Potential Recovery":"sum"
}).reset_index()

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=g1_df_2026['Date'], y=g1_df_2026['Gross Exposure'], name='Gross Exposure', line=dict(color='#004A7C', width=2)))
fig1.add_trace(go.Scatter(x=g1_df_2026['Date'], y=g1_df_2026['Net Exposure'], name='Net Exposure', line=dict(color='#EF4444', width=4)))
fig1.add_trace(go.Scatter(x=g1_df_2026['Date'], y=g1_df_2026['Potential Recovery'], name='Potential Recovery', line=dict(color='#F59E0B', width=2, dash='dash')))

fig1.add_vline(x=datetime.date(2026, 2, 25), line_width=2, line_dash="dash", line_color="gray")
fig1.update_layout(height=450, margin=dict(l=0,r=0,t=0,b=0), template="plotly_white", legend=dict(orientation="h", y=1.1),
                  xaxis_title="2026 Timeline", yaxis_title="USD ($)")
draw_graph_card("G1: Strategic Exposure Trend (Full Year 2026)", "Dotted line represents current date: Feb 25, 2026.", fig1)

st.markdown('<div class="section-title">II. Geographic & Portfolio Impact</div>', unsafe_allow_html=True)
r2_c1, r2_c2 = st.columns(2)

with r2_c1:
    impact_df = f_df.groupby("Therapeutic Area").agg({"Mitigation Forecast": "sum", "Net Exposure": "sum"}).reset_index()
    impact_melted = impact_df.melt(id_vars="Therapeutic Area", var_name="Type", value_name="Value")
    fig2 = px.bar(impact_melted, x="Therapeutic Area", y="Value", color="Type", 
                 color_discrete_map={"Mitigation Forecast": "#10B981", "Net Exposure": "#EF4444"},
                 barmode="stack", height=400)
    draw_graph_card("G2: Duty Impact by Therapeutic Area", "Stacked view of Net Exposure vs. Mitigated Duty.", fig2)

with r2_c2:
    fig3 = px.imshow(f_df.pivot_table(index='Country', columns='Therapeutic Area', values='Net Exposure', aggfunc='sum'), 
                     color_continuous_scale='Reds', height=400)
    draw_graph_card("G3: Geographic Exposure Heatmap", "Net Exposure concentration by TA and Country.", fig3)

st.markdown('<div class="section-title">III. Strategy Drill-Down: Actionable Recovery Levers</div>', unsafe_allow_html=True)
# Moved Pareto (G4) into the Strategy section to help selection
r3_c1, r3_c2 = st.columns([1, 1])

with r3_c1:
    pareto = f_df.groupby("Product")["Potential Recovery"].sum().sort_values(ascending=True).reset_index()
    fig4 = px.bar(pareto, x="Potential Recovery", y="Product", orientation='h', color_discrete_sequence=['#F59E0B'], height=400)
    draw_graph_card("G4: Potential Recovery Pareto", "Highest addressable recovery opportunities.", fig4)

with r3_c2:
    target_products_df = f_df.groupby(["Product", "Category", "Country"]).agg({"Potential Recovery":"sum"}).reset_index().sort_values("Potential Recovery", ascending=False)
    selected_p = st.selectbox("🎯 Select a product to define the execution path:", target_products_df["Product"])
    selected_row = target_products_df[target_products_df["Product"] == selected_p].iloc[0]
    strat = get_realistic_levers(selected_row["Category"], selected_row["Country"])
    
    st.write(f"**Target:** {selected_p} | **Recovery:** ${selected_row['Potential Recovery']/1e3:.1f}K")
    st.info(f"**Strategy:** {strat['Note']}")
    
    fig_pie = px.pie(names=["FTA", "Suspension", "Reclass"], 
                     values=[strat['FTA'], strat['Suspension'], strat['Reclass']], 
                     hole=0.4, height=250, color_discrete_sequence=px.colors.qualitative.Prism)
    fig_pie.update_layout(margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig_pie, use_container_width=True)

# --- 7. AUDIT TABLE ---
st.markdown('<div class="section-title">IV. Transactional Audit Ledger</div>', unsafe_allow_html=True)

audit_display = f_df.sort_values("Date", ascending=False).copy()
cols_to_format = ["Procurement Value", "Gross Exposure", "Mitigation Forecast", "Net Exposure", "Potential Recovery"]
for col in cols_to_format:
    audit_display[col] = audit_display[col].map('{:,.2f}'.format)

st.dataframe(audit_display, use_container_width=True)
