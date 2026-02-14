import streamlit as st

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Techylla Hub", page_icon="🛡️", layout="wide")

# --- 2. BRANDED CSS STYLING ---
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .hub-title { text-align: center; color: #1E3A8A; font-family: 'Segoe UI', sans-serif; font-weight: 700; margin-top: 10px; }
    .hub-subtitle { text-align: center; color: #64748B; margin-bottom: 40px; }
    .module-card {
        background: #F8FAFC; padding: 25px; border-radius: 15px;
        border-top: 5px solid #1E40AF; height: 250px; 
        display: flex; flex-direction: column; justify-content: space-between;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease; margin-bottom: 20px;
    }
    .module-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
    h3 { margin-top: 0; color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HEADER SECTION ---
st.markdown("<h1 class='hub-title'>🛡️ Tariff Management PoC Box</h1>", unsafe_allow_html=True)
st.markdown("<p class='hub-subtitle'>Integrated Trade Intelligence & Strategy Suite</p>", unsafe_allow_html=True)

# --- 4. MODULE GRID SELECTION ---
st.markdown("<h3 style='text-align: center; color: #1E3A8A;'>Select a Strategic Module</h3>", unsafe_allow_html=True)

# ROW 1: Analysis, Mitigation, Simulation
col1, col2, col3 = st.columns(3, gap="large")
with col1:
    st.markdown("<div class='module-card'><div><h3>📊 Analysis</h3><p style='color: #475569;'>HTS Auditing, MFN Rates, FTA Eligibility, and Penalty Detection.</p></div></div>", unsafe_allow_html=True)
    st.link_button("Launch Analysis", "https://techyllatariffiq.streamlit.app/", use_container_width=True)
with col2:
    st.markdown("<div class='module-card'><div><h3>🛠️ Mitigation</h3><p style='color: #475569;'>Execute shield strategies, duty drawbacks, and manage compliance flows.</p></div></div>", unsafe_allow_html=True)
    st.link_button("Launch Mitigation", "https://techyllatariffpro.streamlit.app/", use_container_width=True)
with col3:
    st.markdown("<div class='module-card'><div><h3>🕹️ Simulation</h3><p style='color: #475569;'>Model 2026 sourcing shifts, growth factors, and net tariff impact.</p></div></div>", unsafe_allow_html=True)
    st.link_button("Launch Simulation", "https://techyllatariffsimulation.streamlit.app/", use_container_width=True)

# ROW 2: Tariff Dashboard (4th) | Trade AI (5th)
st.markdown("<br>", unsafe_allow_html=True)
_, col4, col5, _ = st.columns([0.5, 1, 1, 0.5], gap="large")

with col4:
    st.markdown("<div class='module-card' style='border-top-color: #F43F5E;'><div><h3>📈 Tariff Dashboard</h3><p style='color: #475569;'>Comprehensive visibility into procurement spend, tariff impacts, and strategic risk metrics.</p></div></div>", unsafe_allow_html=True)
    st.link_button("Launch Dashboard", "https://techyllatariffdashboard.streamlit.app/", use_container_width=True)

with col5:
    st.markdown("<div class='module-card' style='border-top-color: #8B5CF6;'><div><h3>🤖 Trade AI</h3><p style='color: #475569;'>AI-driven supply chain optimization, risk-weighted sourcing, and cost minimization.</p></div></div>", unsafe_allow_html=True)
    st.link_button("Launch AI", "https://techyllatariffai.streamlit.app/", use_container_width=True)

st.markdown("---")
st.caption("© 2026 Techylla Trade Intelligence. All Rights Reserved.")
