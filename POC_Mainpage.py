import streamlit as st
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Techylla Hub",
    page_icon="🛡️",
    layout="wide" # Set to wide for better horizontal spacing
)

# --- 2. BRANDED CSS STYLING ---
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .hub-title {
        text-align: center;
        color: #1E3A8A;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 700;
        margin-top: 10px;
    }
    .hub-subtitle {
        text-align: center;
        color: #64748B;
        margin-bottom: 40px;
    }
    /* Module Card Styling */
    .module-card {
        background: #F8FAFC;
        padding: 25px;
        border-radius: 15px;
        border-top: 5px solid #1E40AF; /* Changed to top border for horizontal look */
        height: 280px; /* Fixed height for symmetry */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    .module-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    /* Button inside card */
    .stButton button {
        width: 100%;
        font-weight: 600;
        background-color: #FFFFFF;
        color: #1E40AF;
        border: 2px solid #E2E8F0;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGO & HEADING ---
t_col1, t_col2, t_col3 = st.columns([1, 1, 1])

with t_col2:
    logo_path = "techyllalogo.png" 
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #1E40AF;'>TECHYLLA</h2>", unsafe_allow_html=True)

st.markdown("<h1 class='hub-title'>Tariff Management PoC Box</h1>", unsafe_allow_html=True)
st.markdown("<p class='hub-subtitle'>Integrated Trade Intelligence & Strategy Suite</p>", unsafe_allow_html=True)

# --- 4. NAVIGATION MODULES (LEFT TO RIGHT) ---
st.write("###")
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
        <div class='module-card'>
            <div>
                <h3>📊 Analysis</h3>
                <p style='color: #475569;'>HTS Auditing, MFN Rates, FTA Eligibility, and Penalty Detection.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.link_button("Launch Analysis", "https://techyllatariffiq.streamlit.app/", use_container_width=True)

with col2:
    st.markdown("""
        <div class='module-card'>
            <div>
                <h3>🛠️ Mitigation</h3>
                <p style='color: #475569;'>Execute shield strategies, duty drawbacks, and manage compliance flows.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.link_button("Launch Mitigation", "https://techyllatariffpro.streamlit.app/", use_container_width=True)

with col3:
    st.markdown("""
        <div class='module-card'>
            <div>
                <h3>🕹️ Simulation</h3>
                <p style='color: #475569;'>Model 2026 sourcing shifts, growth factors, and net tariff impact.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.link_button("Launch Simulation", "https://techyllatariffsimulation.streamlit.app/", use_container_width=True)

# --- 5. FOOTER ---
st.write("###")
st.write("###")
st.divider()
st.markdown("<p style='text-align: center; color: #94A3B8;'>© 2026 Techylla | Internal PoC Environment</p>", unsafe_allow_html=True)
