import streamlit as st

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Techylla Hub",
    page_icon="📦",
    layout="centered"
)

# --- 2. CUSTOM STYLING ---
st.markdown("""
    <style>
    .main {
        background-color: #F8FAFC;
    }
    .stButton button {
        width: 100%;
        height: 60px;
        font-weight: bold;
        font-size: 18px !important;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        border-color: #1E40AF;
        color: #1E40AF;
        transform: translateY(-2px);
    }
    .hub-title {
        text-align: center;
        color: #1E3A8A;
        font-family: 'Helvetica', sans-serif;
        padding-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HEADING ---
st.markdown("<h1 class='hub-title'>🛡️ Techylla Tariff Management PoC Box</h1>", unsafe_allow_html=True)
st.write("---")
st.info("Select a module below to launch the specific Trade Intelligence tool.")

# --- 4. NAVIGATION BUTTONS ---
# Using columns to create a stacked "Box" feel
col1, col2, col3 = st.columns([1, 5, 1])

with col2:
    st.write("###")
    
    # Module 1: Analysis
    st.link_button(
        "📊 Tariff Rate Analysis", 
        "https://techyllatariffiq.streamlit.app/", 
        use_container_width=True
    )
    st.caption("Identify MFN rates, FTA eligibility, and penalty risks for HTS codes.")

    st.write("###")
    
    # Module 2: Mitigation
    st.link_button(
        "🛠️ Tariff Mitigation Manager", 
        "https://techyllatariffpro.streamlit.app/", 
        use_container_width=True
    )
    st.caption("Execute shield strategies and manage FTA documentation flows.")

    st.write("###")
    
    # Module 3: Simulation
    st.link_button(
        "🕹️ Import Strategy Simulation", 
        "https://techyllatariffsimulation.streamlit.app/", 
        use_container_width=True
    )
    st.caption("Model 2026 procurement shifts, growth factors, and net tariff impact.")

# --- 5. FOOTER ---
st.write("###")
st.divider()
st.caption("© 2026 Techylla | Internal PoC Environment")