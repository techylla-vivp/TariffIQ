import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import re

# --- 1. CORE ENGINE (Synced with Techylla TariffIQ V5) ---
def get_audit_result(target_iso, hts_code):
    """
    Strict implementation of V5 logic:
    MFN Rate -> FTA Search -> Penalty Eval -> Shield Check
    """
    clean_code = hts_code.replace('.', '')
    url = f"https://hts.usitc.gov/reststop/search?keyword={clean_code}"
    
    # Defaults
    base, penalty = 0.05, 0.0
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        record = next((r for r in data if r.get('htsno', '').replace('.', '') == clean_code), data[0] if data else {})
        
        # [STEP 1] MFN General Rate
        base = float(record.get('general', '0%').split('%')[0]) / 100
        
        # [STEP 2] FTA Regex (USMCA Focus)
        spec = record.get('special', '')
        if target_iso in ["MX", "CA"] and ("CA" in spec or "MX" in spec):
            base = 0.0  
        
        # [STEP 3] Penalty Evaluation (Section 301)
        if target_iso == "CN":
            penalty = 0.25 
        
        # [STEP 4] Shield Verification
        if any(x in clean_code for x in ["3004", "8541", "2804"]):
            penalty = 0.0
            
        return base + penalty
    except:
        return 0.05

# --- 2. CONFIGURATION & UI ---
st.set_page_config(layout="wide", page_title="Techylla TariffIQ Strategy")
country_map = {
    "IN": "India (IN)", "CN": "China (CN)", "MX": "Mexico (MX)", 
    "CA": "Canada (CA)", "BE": "Belgium (BE)", "US": "USA (US)"
}
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

st.title("🛡️ Techylla TariffIQ: Strategy Simulation")

# --- 3. BASELINE INPUTS ---
with st.container():
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        mat_name = st.text_input("Material Name", "Industrial Resin B")
        hsn_input = st.text_input("HSN Code", "3908.90.00")
    with c2:
        origin_label = st.selectbox("Baseline Country", list(country_map.values()))
        origin_iso = origin_label[-3:-1]
    with c3:
        base_rate = get_audit_result(origin_iso, hsn_input)
        st.metric("Baseline Duty Rate", f"{base_rate*100:.1f}%")

# --- 4. 2026 PURCHASE PLAN (EDITABLE) ---
st.subheader("1. Monthly Purchase Plan")
init_df = pd.DataFrame({
    "Month": months,
    "Product": [mat_name] * 12,
    "HSN": [hsn_input] * 12,
    "Source": [origin_label] * 12,
    "Qty (MT)": [1000] * 12,
    "Unit Rate ($)": [2150.0] * 12
})
editable_plan = st.data_editor(init_df, use_container_width=True, hide_index=True)

# --- 5. SIMULATION PARAMETERS (SIDEBAR) ---
st.sidebar.header("🕹️ Simulation Engine")
sim_start_month = st.sidebar.selectbox("Start Simulation From", months, index=6)
start_idx = months.index(sim_start_month)

growth_pct = st.sidebar.slider("Growth in Value (%)", -20, 100, 0) / 100

st.sidebar.subheader("Sourcing Shift")
selected_targets = st.sidebar.multiselect("Shift To Countries", list(country_map.keys()), default=["IN"])

allocations, overrides = {}, {}
rem_vol = 100
for iso in selected_targets:
    st.sidebar.markdown(f"**{country_map[iso]}**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        val = st.number_input(f"% Allocation: {iso}", 0, rem_vol, 0)
        allocations[iso] = val / 100
        rem_vol -= val
    with col2:
        auto_r = get_audit_result(iso, hsn_input) * 100
        overrides[iso] = st.number_input(f"Tariff Rate %: {iso}", value=float(auto_r), step=0.1) / 100

# --- 6. DATA PROCESSING ---
results, chart_data = [], []
s_gross_total, s_mit_total, s_net_total = 0.0, 0.0, 0.0

for i, row in editable_plan.iterrows():
    p_qty, p_rate = row["Qty (MT)"], row["Unit Rate ($)"]
    p_val = p_qty * p_rate
    baseline_tariff = p_val * base_rate
    
    # Apply Growth and Shift only from start_idx
    if i < start_idx:
        s_val, s_net, s_mit = p_val, baseline_tariff, 0.0
        chart_data.append({"Month": row["Month"], "Country": origin_label, "Volume": p_qty})
    else:
        s_val = p_val * (1 + growth_pct)
        s_qty = p_qty * (1 + growth_pct)
        # Apply sourcing shift
        weighted_tax = 0.0
        for iso, weight in allocations.items():
            if weight > 0:
                weighted_tax += (s_val * weight * overrides.get(iso, 0))
                chart_data.append({"Month": row["Month"], "Country": country_map[iso], "Volume": s_qty * weight})
        
        # Remaining volume stays baseline
        if rem_vol > 0:
            weighted_tax += (s_val * (rem_vol/100) * base_rate)
            chart_data.append({"Month": row["Month"], "Country": origin_label, "Volume": s_qty * (rem_vol/100)})
            
        s_net = weighted_tax
        s_mit = max(0, (s_val * base_rate) - s_net)

    # Accumulate for Full Year 2026 Scenario
    s_gross_total += (s_val * base_rate)
    s_net_total += s_net
    s_mit_total += s_mit

    results.append({
        "Month": row["Month"],
        "Gross Tariff": baseline_tariff,
        "Realised Mitigation": s_mit,
        "Net Tariff": s_net
    })

res_df = pd.DataFrame(results)
chart_df = pd.DataFrame(chart_data)

# --- 7. KPI DASHBOARDS ---
st.divider()
st.subheader("Annual Simulated Scenario KPIs (Full Year 2026)")
s1, s2, s3 = st.columns(3)
s1.metric("Simulated Gross Tariff", f"${s_gross_total:,.0f}")
s2.metric("Simulated Mitigation", f"${s_mit_total:,.0f}")
s3.metric("Simulated Net Tariff", f"${s_net_total:,.0f}", 
          delta=f"{((s_net_total/res_df['Gross Tariff'].sum() - 1)*100) if res_df['Gross Tariff'].sum() > 0 else 0:.1f}% vs Baseline", 
          delta_color="inverse")

# --- 8. MONTHLY COMPARISON TABLE ---
st.write("### 📅 2026 Monthly Comparison Detail")
st.dataframe(res_df.style.format("${:,.0f}", subset=["Gross Tariff", "Realised Mitigation", "Net Tariff"]), use_container_width=True)

# --- 9. GRAPH (TOWARDS THE END) ---
st.write("---")
st.subheader("📊 Strategic Sourcing & Tariff Liability Analytics")

fig = make_subplots(specs=[[{"secondary_y": True}]])
countries = chart_df["Country"].unique()
colors = px.colors.qualitative.Prism

for idx, country in enumerate(countries):
    c_data = chart_df[chart_df["Country"] == country]
    fig.add_trace(go.Bar(x=c_data["Month"], y=c_data["Volume"], name=f"Vol: {country}", marker_color=colors[idx % len(colors)]), secondary_y=False)

fig.add_trace(go.Scatter(x=res_df["Month"], y=res_df["Net Tariff"], name="Net Tariff ($)", line=dict(color="#EF4444", width=4), mode="lines+markers"), secondary_y=True)

fig.update_layout(title_text="Monthly Country Allocation (Bars) vs. Net Tariff (Line)", barmode="stack", hovermode="x unified", legend=dict(orientation="h", y=1.1))
fig.update_yaxes(title_text="Volume (MT)", secondary_y=False)
fig.update_yaxes(title_text="Net Tariff ($)", secondary_y=True)

st.plotly_chart(fig, use_container_width=True)