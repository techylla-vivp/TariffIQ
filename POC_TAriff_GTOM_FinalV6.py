import streamlit as st
import requests
import re
from datetime import datetime

# --- 1. CORE ENGINE (Restored Precise Matching & Descending Search) ---
def get_hts_data(hts_code):
    clean_code = hts_code.replace('.', '')
    url = f"https://hts.usitc.gov/reststop/search?keyword={clean_code}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if not data: return None
        for record in data:
            if record.get('htsno', '').replace('.', '') == clean_code:
                return record
        return data[0]
    except:
        return None

def parse_rate(rate_str):
    """Restored robust parsing for complex USITC rate strings."""
    if not rate_str or 'free' in rate_str.lower(): return 0.0
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", rate_str)
    return float(nums[0]) / 100.0 if nums else 0.0

# --- 2. THEME & UI (FIXED BUTTON VISIBILITY) ---
st.set_page_config(page_title="Techylla TariffIQ", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #1E40AF !important; }
    
    /* Target only labels and headers for white text */
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1 { 
        color: white !important; 
    }

    /* FIX: Force Sidebar Button to be visible and prominent */
    [data-testid="stSidebar"] button {
        background-color: #38BDF8 !important; /* Sky Blue background */
        color: #0F172A !important;           /* Dark Navy text for contrast */
        border: none !important;
        font-weight: bold !important;
        width: 100% !important;
    }

    /* Keep input fields dark for readability */
    [data-testid="stSidebar"] input, [data-testid="stSidebar"] select {
        color: #1E293B !important; 
    }

    /* Metric & Audit Styles */
    div[data-testid="stMetric"] {
        background-color: #F8FAFC; border: 1px solid #E2E8F0;
        border-top: 4px solid #1E40AF; padding: 15px; border-radius: 8px;
    }
    .audit-log {
        background-color: #0F172A; color: #38BDF8; font-family: monospace;
        padding: 20px; border-radius: 8px; line-height: 1.5; font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. INPUT SECTION (Full Country Map) ---
country_map = {
    "IN": "India (IN)", "CN": "China (CN)", "MX": "Mexico (MX)", 
    "CA": "Canada (CA)", "SG": "Singapore (SG)", "KR": "South Korea (KR)", 
    "BE": "Belgium (BE)", "DE": "Germany (DE)"
}

st.sidebar.title("🛡️ Techylla TariffIQ")
user_profile = st.sidebar.selectbox("Simulation Profile:", ["Strategic Partner", "Standard Importer"])
origin_label = st.sidebar.selectbox("Country of Origin", list(country_map.values()))
origin_iso = origin_label[-3:-1] 
hts_input = st.sidebar.text_input("Enter HTS Code:", "3004.90.92.15")
shipment_value = st.sidebar.number_input("Shipment Value (USD)", min_value=0.0, value=100000.0)
run_audit = st.sidebar.button("Run Strategic Audit")

# --- 4. 2026 CALCULATION LOGIC (V13 Updated for 15% S122) ---
def get_audit_result(iso, hts, record):
    base_rate = parse_rate(record.get('general', '0.0%'))
    spec_rate = record.get('special', 'N/A')
    
    # FTA Check (S/MX symbols from original V5)
    fta_codes = {'MX': ['S', 'MX'], 'CA': ['S', 'CA'], 'KR': ['KR'], 'SG': ['SG']}
    is_fta_active = any(sym in spec_rate for sym in fta_codes.get(iso, []))
    if is_fta_active: base_rate = 0.0

    # Section 122 Surcharge (15% statutory max effective Feb 24, 2026)
    surcharge_rate = 0.15
    p_type = "SECTION 122 SURCHARGE"

    if iso in ["MX", "CA"]:
        p_type, surcharge_rate = "USMCA Partnership", 0.0

    # SHIELD LOGIC: TrumpRx / Breaking Ground eligibility
    shield, shield_multiplier = "NONE", 1.0
    if user_profile == "Strategic Partner" and hts.startswith("30"):
        shield = "TRUMPRX / MFN SHIELD ACTIVE"
        shield_multiplier = 0.0 
    elif user_profile == "Strategic Partner":
        shield = "ELIGIBILITY DENIED (NON-PHARMA)"
    
    penalty = surcharge_rate * shield_multiplier
    total_rate = base_rate + penalty
    return base_rate, penalty, shield, p_type, is_fta_active, total_rate

# --- 5. EXECUTION & RESULTS (Full Feature Restore) ---
if run_audit:
    clean_code = hts_input.replace('.', '')
    levels = [clean_code[:4], clean_code[:6], clean_code]
    full_path_desc, final_record = [], None

    with st.spinner('Syncing Global Intelligence Nodes...'):
        for lvl in levels:
            record = get_hts_data(lvl)
            if record:
                desc = record.get('description', 'N/A').replace('<i>', '').replace('</i>', '').strip()
                full_path_desc.append(desc)
                if len(lvl) >= 8: final_record = record

    if final_record:
        base, penalty, shield, p_type, fta_applied, total_rate = get_audit_result(origin_iso, clean_code, final_record)
        
        st.write(f"## {user_profile}: Strategic Trade Audit")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Base Duty", f"{base*100:.1f}%")
        m2.metric("2026 Surcharge", f"{penalty*100:.1f}%", delta=p_type if penalty > 0 else "Exempt")
        m3.metric("Shield Status", "ACTIVE" if "ACTIVE" in shield else "INACTIVE")
        m4.metric("Effective Duty", f"{total_rate*100:.1f}%")

        # Audit Log (Restored)
        st.write("### 🔍 Compliance Audit Trail")
        audit_text = f"""
[TIMESTAMP]: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
[STEP 1]: MFN General Rate identified as {base*100:.1f}%
[STEP 2]: FTA/USMCA Search: {'MATCH FOUND' if fta_applied else 'NO MATCH'}
[STEP 3]: Surcharge Evaluation: {p_type} (+{penalty*100:.1f}%)
[STEP 4]: Shield Verification: {shield}
[RESULT]: Final Effective Rate: {total_rate*100:.1f}%
        """
        st.markdown(f'<div class="audit-log"><pre>{audit_text}</pre></div>', unsafe_allow_html=True)

        # Hierarchy Path (Restored)
        st.divider()
        st.write("### 📋 Commodity Intelligence")
        path_html = " ➔ ".join(full_path_desc)
        st.markdown(f'<div class="path-container"><b>Hierarchy Path:</b><br>{path_html}</div>', unsafe_allow_html=True)

        # Benchmark Table (Restored)
        st.write("### ⚖️ Global Sourcing Benchmarks")
        comp_rows = []
        for iso, name in country_map.items():
            b, p, s, pt, f, tr = get_audit_result(iso, clean_code, final_record)
            comp_rows.append({
                "Country": name, "Trade Regime": pt,
                "Status": "🛡️ Shielded" if "ACTIVE" in s else ("✅ FTA Match" if f else "Standard"),
                "Tax Rate": f"{tr*100:.1f}%",
                "Est. Duty USD": f"${(shipment_value * tr):,.2f}"
            })
        st.table(comp_rows)
    else:
        st.error("HTS Code not found. Please verify classification.")