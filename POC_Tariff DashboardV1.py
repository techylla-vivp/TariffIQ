import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURATION ---
st.set_page_config(layout="wide", page_title="TariffIQ Scenario Simulator")
countries = {"IN": "India", "CN": "China", "MX": "Mexico", "CA": "Canada", "US": "USA", "DE": "Germany", "ES": "Spain", "FR": "France"}

# Initialize Scenario Vault in Session State
if 'vault' not in st.session_state:
    st.session_state.vault = {}

st.title("🛡️ Techylla TariffIQ: Simulator")
st.markdown("Run multi-dimensional scenarios to evaluate supply chain resilience against tariff hikes.")

# --- 2. BASELINE PURCHASE PLAN (Boehringer Ingelheim Focus) ---
st.subheader("1. 2026 Baseline Purchase Plan")
with st.expander("Edit Boehringer Ingelheim Portfolio", expanded=True):
    init_data = [
        {"Product": "Jardiance (Human Health)", "HTS": "3004.90.92", "Origin": "DE", "Destination": "US", "Procurement Value ($)": 74000000, "Tariff Rate (%)": 0.0},
        {"Product": "Spiriva (Respiratory)", "HTS": "3004.90.91", "Origin": "ES", "Destination": "US", "Procurement Value ($)": 38000000, "Tariff Rate (%)": 0.0},
        {"Product": "NexGard (Animal Health)", "HTS": "3004.90.92", "Origin": "FR", "Destination": "US", "Procurement Value ($)": 13500000, "Tariff Rate (%)": 0.0},
        {"Product": "Precision Medical Tools", "HTS": "9018.90.00", "Origin": "DE", "Destination": "US", "Procurement Value ($)": 5000000, "Tariff Rate (%)": 4.5},
        {"Product": "Active Ingredients (API)", "HTS": "2933.39.00", "Origin": "CN", "Destination": "US", "Procurement Value ($)": 12000000, "Tariff Rate (%)": 10.0},
    ]
    # captured from data_editor to ensure updates reflect in charts
    df_plan = st.data_editor(pd.DataFrame(init_data), use_container_width=True, num_rows="dynamic", key="main_editor")

# --- 3. SCENARIO BUILDER ---
st.sidebar.header("🕹️ Scenario Manager")
# Updated dropdown options as requested
scenario_type = st.sidebar.selectbox(
    "Select Scenario Type",
    options=[" Global Change", " Country-specific Change", "Product-specific Change", "Targeted (HTS + Country)"]
)

hike_val = st.sidebar.slider("Tariff Hike (%)", 0, 100, 15) / 100

st.sidebar.subheader("🛡️ Exemption Shield")
shielded_countries = st.sidebar.multiselect("Shielded Countries", list(countries.keys()), default=["MX", "CA"], help="Countries exempt from Section 122 duties.")
shielded_hts_prefixes = st.sidebar.text_input("Shielded HTS Prefixes", "3004", help="HTS codes exempt (e.g., 30 for Pharma).").split(",")

target_countries, target_hts = [], []
if scenario_type == " Country-specific Change":
    target_countries = st.sidebar.multiselect("Select Countries", list(countries.keys()))
elif scenario_type == "Product-specific Change":
    target_hts = st.sidebar.multiselect("Select HTS Codes", df_plan["HTS"].unique())
elif scenario_type == "Targeted (HTS + Country)":
    target_countries = st.sidebar.multiselect("Select Countries", list(countries.keys()))
    target_hts = st.sidebar.multiselect("Select HTS Codes", df_plan["HTS"].unique())

# --- 4. SIMULATION CALCULATION ---
def calculate_impact(row):
    base_rate = row["Tariff Rate (%)"] / 100
    p_val = row["Procurement Value ($)"]
    base_tariff_amt = p_val * base_rate
    
    apply_hike = False
    if scenario_type == " Global Change": apply_hike = True
    elif scenario_type == " Country-specific Change" and row["Origin"] in target_countries: apply_hike = True
    elif scenario_type == "Product-specific Change" and row["HTS"] in target_hts: apply_hike = True
    elif scenario_type == "Targeted (HTS + Country)" and row["Origin"] in target_countries and row["HTS"] in target_hts: apply_hike = True
    
    is_shielded_country = row["Origin"] in shielded_countries
    is_shielded_hts = any(row["HTS"].startswith(prefix.strip()) for prefix in shielded_hts_prefixes if prefix.strip())
    
    if is_shielded_country or is_shielded_hts:
        apply_hike = False 
    
    sim_rate = base_rate + hike_val if apply_hike else base_rate
    sim_tariff_amt = p_val * sim_rate
    rate_change = (sim_rate - base_rate) * 100
    
    return pd.Series([base_tariff_amt, sim_tariff_amt, sim_rate * 100, rate_change])

df_plan[['Base Tariff $', 'Simulated Tariff $', 'New Rate %', 'Rate Change (%)']] = df_plan.apply(calculate_impact, axis=1)

# --- 5. VISUALIZATION & COMPARISON ---
st.divider()
c1, c2, c3 = st.columns(3)
total_base = df_plan['Base Tariff $'].sum()
total_sim = df_plan['Simulated Tariff $'].sum()
delta = total_sim - total_base

c1.metric("Baseline Annual Tariff", f"${total_base:,.0f}")
c2.metric("Simulated Annual Tariff", f"${total_sim:,.0f}", delta=f"${delta:,.0f}", delta_color="inverse")
c3.metric("Cost Increase (%)", f"{(delta/total_base*100) if total_base > 0 else 0:.1f}%")

st.subheader("📊 Strategic Impact Analysis")
fig = go.Figure()
fig.add_trace(go.Bar(name='Baseline (Pre-S122)', x=df_plan['Product'], y=df_plan['Base Tariff $'], marker_color='#1E3A8A'))
fig.add_trace(go.Bar(name='Simulation (S122 Hike)', x=df_plan['Product'], y=df_plan['Simulated Tariff $'], marker_color='#EF4444'))

if st.session_state.vault:
    compare_with = st.sidebar.multiselect("Compare with Saved Scenario", list(st.session_state.vault.keys()))
    for sc_name in compare_with:
        saved_df = st.session_state.vault[sc_name]
        fig.add_trace(go.Bar(name=f"Saved: {sc_name}", x=saved_df['Product'], y=saved_df['Simulated Tariff $']))

fig.update_layout(barmode='group', height=400, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig, use_container_width=True)

st.write("### 🔍 Line-Item Comparison & Exemption Analysis")
def style_table(val):
    if val > 0: return 'color: red; font-weight: bold'
    if val == 0: return 'color: #059669; font-weight: bold' 
    return 'color: black'

st.dataframe(
    df_plan.style.format({
        "Procurement Value ($)": "${:,.0f}", 
        "Tariff Rate (%)": "{:.1f}%",
        "Base Tariff $": "${:,.0f}", 
        "Simulated Tariff $": "${:,.0f}",
        "New Rate %": "{:.1f}%", 
        "Rate Change (%)": "+{:.1f}%"
    }).map(style_table, subset=['Rate Change (%)']),
    use_container_width=True
)

# --- 6. SAVE SCENARIO ---
st.sidebar.divider()
sc_name_input = st.sidebar.text_input("Scenario Name", "Pharma Shield Active")
if st.sidebar.button("💾 Save Current Scenario"):
    st.session_state.vault[sc_name_input] = df_plan.copy()
    st.sidebar.success(f"'{sc_name_input}' saved. Use the multiselect above to compare.")
