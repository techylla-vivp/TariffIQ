import streamlit as st
import requests
import re
from datetime import datetime

# --- 1. CORE ENGINE ---
def get_hts_data(hts_code):
    clean_code = hts_code.replace('.', '')
    url = f"https://hts.usitc.gov/reststop/search?keyword={clean_code}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        for record in data:
            # RESTORED: Precise matching for htsno per original requirements
            if record.get('htsno', '').replace('.', '') == clean_code:
                return record
        return data[0] if data else None
    except:
        return None

# --- 2. THEME & UI ---
st.set_page_config(page_title="Techylla TariffIQ", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #1E40AF !important; }
    [data-testid="stSidebar"] * { color: white !important; }
    div[data-testid="stMetric"] {
        background-color: #F8FAFC; border: 1px solid #E2E8F0;
        border-top: 4px solid #1E40AF; padding: 15px; border-radius: 8px;
    }
    .path-container {
        background-color: #F1F5F9; border-left: 6px solid #1E40AF;
        padding: 20px; border-radius: 8px; color: #1E293B !important;
    }
    .audit-log {
        background-color: #0F172A; color: #38BDF8; font-family: monospace;
        padding: 15px; border-radius: 5px; line-height: 1.5; font-size: 0.85rem;
    }
    .shield-box {
        background-color: #ECFDF5; border: 1px solid #10B981;
        padding: 15px; border-radius: 8px; color: #065F46;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. BRANDED HEADER ---
st.markdown("""
    <div style="padding: 10px 0px 20px 0px;">
        <h1 style="color: #1E40AF; margin-bottom: 0;">🛡️ Techylla TariffIQ</h1>
        <p style="font-size: 1.1rem; color: #475569; font-weight: 500;"> Strategic Global Trade & Duty Optimization Node | Feb 2026</p>
    </div>
""", unsafe_allow_html=True)

# --- 4. INPUT SECTION ---
country_map = {
    "IN": "India (IN)",
    "CN": "China (CN)",
    "MX": "Mexico (MX)",
    "CA": "Canada (CA)",
    "SG": "Singapore (SG)",
    "KR": "South Korea (KR)",
    "BE": "Belgium (BE)"
}

with st.container():
    col_a, col_b, col_c = st.columns([2, 1, 1])
    with col_a:
        full_hts = st.text_input("Enter HTS/HSN Code (e.g., 2833.22.00)", "2833.22.00")
    with col_b:
        origin_label = st.selectbox("Country of Origin", list(country_map.values()))
        origin_iso = origin_label[-3:-1] 
    with col_c:
        value = st.number_input("Shipment Value (USD)", min_value=0.0, value=10000.0)

# --- 5. CALCULATION WRAPPER ---
def get_audit_result(target_origin, target_code, record):
    gen_rate_str = record.get('general', '0.0%')
    spec_rate = record.get('special', 'N/A')
    
    try:
        base_calc = float(gen_rate_str.split('%')[0]) / 100 if "%" in gen_rate_str else 0.0
    except:
        base_calc = 0.0

    # FTA regex logic
    fta_codes = {'MX': ['S', 'MX'], 'CA': ['S', 'CA'], 'KR': ['KR'], 'SG': ['SG']}
    is_fta_active = False
    if target_origin in fta_codes:
        for symbol in fta_codes[target_origin]:
            pattern = rf"[^A-Z]{symbol}[^A-Z]|^{symbol}[^A-Z]|[^A-Z]{symbol}$"
            if re.search(pattern, spec_rate) or f"({symbol})" in spec_rate:
                base_calc, is_fta_active = 0.0, True
                break

    # 2026 PENALTY LOGIC
    penalty_rate, shield_name, p_type = 0.0, "NONE", "None"
    shield_reason = ""
    
    if target_origin == "IN":
        p_type = "Feb 2026 US-India Interim Deal"
        penalty_rate = max(0.0, 0.18 - base_calc)
        
        # EXPANDED SHIELD CATEGORIES
        infra_shields = {
            ('3906', '3907'): "Water Treatment Polymers (Coagulants/Flocculants)",
            ('2827', '2833'): "Water Purification Salts (Chlorides/Sulfates)",
            ('3808', '3824'): "Industrial Disinfectants & Binders",
            ('3214',): "Infrastructure Sealants & Construction Cements"
        }
        
        for prefixes, reason in infra_shields.items():
            if target_code.startswith(prefixes):
                penalty_rate, shield_name = 0.0, "9903.01.32 (Infra & Water Shield)"
                shield_reason = reason
                break
            
    elif target_origin == "KR":
        p_type = "South Korea Escalation (Jan 27)"
        if not is_fta_active:
            penalty_rate = max(0.0, 0.25 - base_calc)
        
    elif target_origin == "CN":
        p_type = "Section 301 + Reciprocal Stack"
        penalty_rate = 0.35
        
    return base_calc, penalty_rate, shield_name, p_type, is_fta_active, shield_reason

# --- 6. EXECUTION ---
if st.button("🚀 Run Strategic Audit"):
    clean_code = full_hts.replace('.', '')
    levels = [clean_code[:4], clean_code[:6], clean_code]
    full_path_desc, final_record = [], None

    with st.spinner('Syncing Compliance Nodes...'):
        for lvl in levels:
            record = get_hts_data(lvl)
            if record:
                desc = record.get('description', 'N/A').replace('<i>', '').replace('</i>', '').strip()
                full_path_desc.append(desc)
                if len(lvl) >= 8: final_record = record

    if final_record:
        base, penalty, shield, p_type, fta_applied, s_reason = get_audit_result(origin_iso, clean_code, final_record)
        total_rate = base + penalty
        total_usd = value * total_rate

        # --- RESULTS UI ---
        r1, r2, r3 = st.columns(3)
        r1.metric("Base Duty Rate", f"{base*100:.1f}%")
        r2.metric("Penalty Impact", f"{penalty*100:.1f}%", help=p_type)
        r3.metric("Total Est. Tax USD", f"${total_usd:,.2f}", delta=f"{total_rate*100:.1f}%", delta_color="inverse")

        # --- SHIELD ELIGIBILITY BOX ---
        if shield != "NONE":
            st.markdown(f"""
            <div class="shield-box">
                <strong>🛡️ 9903.01.32 Eligibility Confirmed</strong><br>
                This HTS code is classified as <b>{s_reason}</b>. 
                Under the Feb 7, 2026 US-India Deal, this shipment is exempt from the 18% reciprocal penalty.
            </div>
            """, unsafe_allow_html=True)

        # --- AUDIT LOG ---
        st.write("### 📜 Internal Audit Log")
        audit_text = f"""
        [TIMESTAMP]: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        [HTS_CODE]: {clean_code} | [ORIGIN]: {country_map[origin_iso]}
        [STEP 1]: MFN General Rate identified as {base*100:.1f}%
        [STEP 2]: FTA Regex Search: {'MATCH FOUND' if fta_applied else 'NO MATCH'}
        [STEP 3]: Penalty Evaluation: {p_type} (+{penalty*100:.1f}%)
        [STEP 4]: Shield Verification: {f'SHIELD TRIGGERED ({shield})' if shield != 'NONE' else 'NOT ELIGIBLE'}
        [RESULT]: Final Effective Rate: {total_rate*100:.1f}%
        """
        st.markdown(f'<div class="audit-log"><pre>{audit_text}</pre></div>', unsafe_allow_html=True)

        st.divider()
        st.write("### 📋 Commodity Intelligence")
        path_html = " ➔ ".join(full_path_desc)
        st.markdown(f'<div class="path-container"><b>Hierarchy Path:</b><br>{path_html}</div>', unsafe_allow_html=True)

        # --- 7. BENCHMARK TABLE ---
        st.write("### ⚖️ Global Sourcing Benchmarks")
        comp_rows = []
        for iso, name in country_map.items():
            b, p, s, pt, f, _ = get_audit_result(iso, clean_code, final_record)
            tr = b + p
            comp_rows.append({
                "Country": name,
                "Trade Regime": pt if pt != "None" else "Standard MFN",
                "Status": "🛡️ Shielded" if s != "NONE" else ("✅ FTA Match" if f else "Standard"),
                "Tax Rate": f"{tr*100:.1f}%",
                "Est. Duty USD": f"${(value * tr):,.2f}"
            })
        st.table(comp_rows)
        
    else:

        st.error("HTS code not found. Please verify.")
