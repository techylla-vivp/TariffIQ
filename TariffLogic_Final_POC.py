import streamlit as st
import requests
import pandas as pd

# --- 1. CORE ENGINE ---
def get_hts_data(hts_code):
    clean_code = hts_code.replace('.', '').strip()
    url = f"https://hts.usitc.gov/reststop/search?keyword={clean_code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if not data: return None
        for record in data:
            if record.get('htsno', '').replace('.', '').startswith(clean_code):
                return record
        return data[0]
    except:
        return None

def is_india_shield_applicable(hts_code):
    prefix = hts_code.replace('.', '').strip()
    strategic_prefixes = ('30', '28', '29', '3808', '3824', '3827', '3906', '3907', '8541', '8542')
    return prefix.startswith(strategic_prefixes)

def calculate_gross_tariff(iso, hts_code, record):
    gen_rate_str = record.get('general', '0.0%')
    try:
        if "Free" in gen_rate_str:
            base_mfn = 0.0
        else:
            base_mfn = float(''.join(filter(lambda x: x.isdigit() or x == '.', gen_rate_str.split('%')[0]))) / 100
    except:
        base_mfn = 0.0
    
    penalty = 0.0
    if iso == "IN": penalty = 0.18
    elif iso == "CN": penalty = 0.35
    elif iso in ["CA", "MX", "KR"]: penalty = 0.25
    return base_mfn + penalty

# --- 2. CONFIG ---
st.set_page_config(page_title="TariffLogic Pro", layout="wide")

country_map = {
    "AU": "Australia", "CA": "Canada (USMCA)", "CN": "China", 
    "IN": "India", "SG": "Singapore", "BE": "Belgium", "KR": "South Korea",
    "MX": "Mexico (USMCA)"
}

if 'realized_flags' not in st.session_state:
    st.session_state.realized_flags = {}
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = {}

st.title("🛡️ TariffLogic Pro: Mitigation Manager")

# --- 3. INPUTS ---
with st.sidebar:
    st.header("📋 Product Specification")
    hsn_input = st.text_input("Enter HSN/HTS Code", "3824.99.93")
    total_val = st.number_input("Total Order Value (USD)", value=100000.0)
    
    st.divider()
    st.header("🌍 Simulation Scope")
    selected_isos = st.multiselect("Select Countries", options=list(country_map.keys()), 
                                   format_func=lambda x: country_map[x], 
                                   default=["SG", "CA", "IN", "CN"])

# --- 4. EXECUTION ---
hts_record = get_hts_data(hsn_input)

if hts_record and selected_isos:
    st.success(f"HTS Found: {hts_record.get('htsno')}")
    sim_data = []
    
    for iso in selected_isos:
        name = country_map[iso]
        
        with st.expander(f"📍 Route: {name}", expanded=True):
            c1, c2, c3 = st.columns([1, 1, 1])
            
            with c1:
                mitigation_options = ["None"]
                if iso in ["AU", "CA", "MX", "SG", "KR"]:
                    mitigation_options.append(f"Apply FTA Certification ({iso})")
                if iso == "IN" and is_india_shield_applicable(hsn_input):
                    mitigation_options.append("Apply Infrastructure Shield")
                if iso == "CN":
                    mitigation_options.append("Section 301 Exclusion Request")
                mitigation_options.append("Duty Drawback (Re-export)")

                system_rate = calculate_gross_tariff(iso, hsn_input, hts_record)
                edited_rate = st.number_input(f"Gross Rate % ({name})", value=float(system_rate*100), key=f"rate_{iso}") / 100
                allocation_val = st.slider(f"Allocation % ({name})", 0, 100, 25, key=f"alloc_{iso}")
                route_val = total_val * (allocation_val / 100)
                gross_amt = route_val * edited_rate
                
                selected_mit = st.selectbox(f"Select Mitigation Strategy ({name})", mitigation_options, key=f"mit_{iso}")
            
            with c2:
                potential_savings = 0.0
                if "FTA" in selected_mit: potential_savings = gross_amt
                elif "Shield" in selected_mit: potential_savings = route_val * 0.18
                elif "Exclusion" in selected_mit: potential_savings = route_val * 0.25
                elif "Drawback" in selected_mit: potential_savings = gross_amt * 0.99
                
                net_forecast_duty = gross_amt - potential_savings
                eff_rate_forecast = (net_forecast_duty / route_val * 100) if route_val > 0 else 0
                
                st.metric("Gross Tariff", f"${gross_amt:,.2f}")
                st.metric("Forecasted Savings", f"${potential_savings:,.2f}")
                st.markdown(f'<p style="color: grey; font-size: 0.85em; margin-top: -15px;">Effective Rate: ({eff_rate_forecast:.1f}%)</p>', unsafe_allow_html=True)
                
                if st.button(f"Confirm Realization", key=f"btn_{iso}"):
                    st.session_state.realized_flags[iso] = True
                    st.rerun()
            
            with c3:
                is_realized = st.session_state.realized_flags.get(iso, False)
                realized_amt = potential_savings if is_realized else 0.0
                net_duty_paid = gross_amt - realized_amt
                st.metric("Realized Mitigation", f"${realized_amt:,.2f}")
                st.metric("Net Tariff", f"${net_duty_paid:,.2f}", delta_color="inverse")
            
            sim_data.append({
                "Route": name,
                "Allocation (%)": allocation_val,
                "Mitigation Strategy": selected_mit,
                "Gross Rate (%)": edited_rate * 100,
                "Gross Tariff ($)": gross_amt,
                "Forecast Savings ($)": potential_savings,
                "Effective Rate (%)": eff_rate_forecast,
                "Realised Mitigation ($)": realized_amt,
                "Net Tariff ($)": net_duty_paid
            })

    # --- 5. SUMMARY TABLE ---
    st.divider()
    # Bold and bigger size for the header
    st.markdown("<h2 style='text-align: center; font-weight: bold;'>📊 GLOBAL MITIGATION SUMMARY</h2>", unsafe_allow_html=True)
    
    summary_df = pd.DataFrame(sim_data)
    
    if not summary_df.empty:
        total_gross = summary_df["Gross Tariff ($)"].sum()
        total_net = summary_df["Net Tariff ($)"].sum()
        total_forecast = summary_df["Forecast Savings ($)"].sum()
        total_alloc = summary_df["Allocation (%)"].sum()
        
        totals = {
            "Route": "TOTAL / AVG",
            "Allocation (%)": total_alloc,
            "Mitigation Strategy": "-",
            "Gross Rate (%)": (total_gross / total_val * 100) if total_val > 0 else 0,
            "Gross Tariff ($)": total_gross,
            "Forecast Savings ($)": total_forecast,
            "Effective Rate (%)": ((total_gross - total_forecast) / (total_val * (total_alloc/100)) * 100) if total_alloc > 0 else 0,
            "Realised Mitigation ($)": summary_df["Realised Mitigation ($)"].sum(),
            "Net Tariff ($)": total_net
        }
        summary_df = pd.concat([summary_df, pd.DataFrame([totals])], ignore_index=True)

    # Style the table to make it look prominent
    st.table(summary_df.style.format({
        "Allocation (%)": "{:.1f}%",
        "Gross Rate (%)": "{:.2f}%",
        "Gross Tariff ($)": "${:,.2f}",
        "Forecast Savings ($)": "${:,.2f}",
        "Effective Rate (%)": "{:.2f}%",
        "Realised Mitigation ($)": "${:,.2f}",
        "Net Tariff ($)": "${:,.2f}"
    }).set_properties(**{'font-weight': 'bold'}, subset=pd.IndexSlice[summary_df.index[-1], :]))

    # --- 6. SCENARIO ANALYSIS ---
    st.divider()
    st.subheader("💾 Scenario Analysis")
    sc_col1, sc_col2 = st.columns(2)
    with sc_col1:
        sc_name = st.text_input("Scenario Name", value="Supply Chain Plan A")
        if st.button("Save Current Scenario"):
            st.session_state.scenarios[sc_name] = summary_df.copy()
            st.success(f"Scenario '{sc_name}' saved.")
    
    if len(st.session_state.scenarios) >= 2:
        st.subheader("⚖️ Compare Scenarios")
        s1 = st.selectbox("Baseline Scenario", options=list(st.session_state.scenarios.keys()), index=0)
        s2 = st.selectbox("Comparison Scenario", options=list(st.session_state.scenarios.keys()), index=1)
        
        res1 = st.session_state.scenarios[s1].iloc[-1]
        res2 = st.session_state.scenarios[s2].iloc[-1]
        
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Net Tariff ({s1})", f"${res1['Net Tariff ($)']:,.2f}")
        m2.metric(f"Net Tariff ({s2})", f"${res2['Net Tariff ($)']:,.2f}", 
                  delta=f"{res2['Net Tariff ($)'] - res1['Net Tariff ($)']:,.2f}", delta_color="inverse")
        m3.metric("Rate Improvement", f"{(res1['Effective Rate (%)'] - res2['Effective Rate (%)']):.2f}%")

else:
    st.info("Select HTS and countries to begin analysis.")