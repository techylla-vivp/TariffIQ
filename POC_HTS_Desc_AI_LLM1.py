import streamlit as st
import pandas as pd
import google.generativeai as genai
from sentence_transformers import SentenceTransformer, util
import torch

# ---------------------------------------------------------
# 1. EMBEDDED DATASET (25 Industry-Specific HTS Records)
# ---------------------------------------------------------
HTS_DATA = [
    # --- HUMAN HEALTH: FINISHED GOODS (3004) ---
    {"desc": "Medicaments and medicine strictly for human use only; human fever treatment pills, tablets, or capsules; internal medicine for people in measured doses; analgesic or antipyretic for humans", "hts": "3004.90", "cat": "Human Health/Finished"},
    {"desc": "Metabolic regulator tablets for human oral use, put up in measured doses for retail sale; human diabetes pills for glucose control", "hts": "3004.90", "cat": "Human Health/Finished"},
    {"desc": "Respiratory inhalation solution for human patients in dosage form with mechanical atomizer; human asthma treatment or bronchodilator", "hts": "3004.90", "cat": "Respiratory/Finished"},
    {"desc": "Kinase inhibitor capsules for human oncology patients, 150mg retail builder packs; human cancer treatment pills", "hts": "3004.90", "cat": "Oncology/Finished"},
    {"desc": "Anticoagulant capsules for human medicine, oral blood thinner in measured doses for people; cardiovascular pills", "hts": "3004.90", "cat": "Cardiovascular/Finished"},
    {"desc": "DPP-4 inhibitor tablets for human diabetic patients, 5mg film-coated for retail sale; glucose management medication", "hts": "3004.90", "cat": "Metabolic/Finished"},
    {"desc": "Antihypertensive tablets for human patients, 80mg dosage for retail sale; human blood pressure pills", "hts": "3004.90", "cat": "Cardiovascular/Finished"},
    {"desc": "Human Insulin; raw unmixed bulk powder of insulin; biosynthetic or recombinant insulin crystal; insulin in measured doses for diabetic therapy; bulk pharmaceutical insulin", "hts": "3004.31", "cat": "Hormones"},
    {"desc": "Antibiotics for human use in measured doses or retail packaging; penicillins or streptomycins for people", "hts": "3004.10", "cat": "Human Health/Antibiotics"},

    # --- ANIMAL HEALTH: FINISHED GOODS (3004) ---
    {"desc": "Veterinary medication strictly for animal use only; tablets, capsules, or boluses for livestock (cattle, buffalo, goat, sheep, horse); animal fever treatment; NOT for human use", "hts": "3004.90", "cat": "Animal Health/Finished"},
    {"desc": "Veterinary chewable tablets for dogs, cats, and pets; flea, tick, and ectoparasite control medication for animals; animal use only", "hts": "3004.90", "cat": "Animal Health/Finished"},
    {"desc": "Veterinary oral suspension or liquid medicament, NSAID dosage for domestic animals or livestock; animal pain relief; not for people", "hts": "3004.90", "cat": "Animal Health/Finished"},

    # --- RAW MATERIALS & APIs (Chapter 29) ---
    {"desc": "Metabolic regulator Active Pharmaceutical Ingredient (API) powder, bulk raw material; generic chemical compounds for metabolic therapy; non-hormonal", "hts": "2933.39", "cat": "Human Health/API"},
    {"desc": "Bronchodilator API, bulk chemical organic compound for human respiratory therapy raw material", "hts": "2933.91", "cat": "Respiratory/API"},
    {"desc": "Kinase inhibitor API for human pulmonary fibrosis or oncology treatment, bulk raw chemical", "hts": "2933.79", "cat": "Oncology/API"},
    {"desc": "Anticoagulant API, raw material for human cardiovascular medication bulk chemical", "hts": "2933.39", "cat": "Cardiovascular/API"},
    {"desc": "DPP-4 inhibitor API for human glucose management, bulk raw powder chemical", "hts": "2933.59", "cat": "Metabolic/API"},
    {"desc": "Angiotensin II receptor antagonist API, bulk human antihypertensive raw material; cardiovascular API", "hts": "2933.39", "cat": "Cardiovascular/API"},
    {"desc": "Veterinary ectoparasiticide API, raw material for animal health products only; bulk chemical for animal use", "hts": "2934.99", "cat": "Animal Health/API"},
    {"desc": "Non-steroidal anti-inflammatory (NSAID) API for veterinary animal use only; bulk raw material", "hts": "2934.10", "cat": "Animal Health/API"},
    {"desc": "Vitamins in bulk form (Cyanocobalamin / Vitamin B12), unmixed raw crystals or powder", "hts": "2936.26", "cat": "Supplements/API"},

    # --- BIOLOGICS, VACCINES & SPECIALTY (3002, 3006) ---
    {"desc": "Monoclonal antibodies (mAbs) for human therapy, immunological products; injectable biologics for people", "hts": "3002.13", "cat": "Biologics"},
    {"desc": "Human vaccines, prophylactic viral or bacterial strains; injectable liquid for people only", "hts": "3002.41", "cat": "Biologics/Vaccines"},
    {"desc": "Veterinary vaccines for livestock animals; injectable liquid biological preparations for animal immunization only; animal viral antigens", "hts": "3002.42", "cat": "Animal Health/Vaccines"},
    {"desc": "Antisera and modified immunological blood fractions for medical therapeutic use; human or animal biologics", "hts": "3002.12", "cat": "Biologics"},
    {"desc": "Sterile surgical suture materials for wound closure; medical surgery supplies; sterile catgut", "hts": "3006.10", "cat": "Medical Supplies"},
    {"desc": "Diagnostic reagents for medical imaging and patient examination; X-ray contrast media or opacifying agents", "hts": "3006.30", "cat": "Diagnostics"},
    {"desc": "Waste pharmaceuticals, expired medicaments or chemicals unfit for use; for destruction only", "hts": "3006.92", "cat": "Compliance/Disposal"}
]

df = pd.DataFrame(HTS_DATA)

# ---------------------------------------------------------
# 2. AI CONFIGURATION
# ---------------------------------------------------------
# Set your API Key
API_KEY = "YOUR_API_KEY_HERE"
genai.configure(api_key=API_KEY)

@st.cache_resource
def load_embed_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

embed_model = load_embed_model()
corpus_embeddings = embed_model.encode(df['desc'].tolist(), convert_to_tensor=True)

# ---------------------------------------------------------
# 3. STREAMLIT UI
# ---------------------------------------------------------
st.set_page_config(page_title="AI Trade POC", layout="wide")

st.title("🛡️ AI-Native HTS Classification Engine")
st.markdown("**Target Business Area:** Life Sciences & Animal Health")

with st.form("classification_form"):
    query = st.text_input("Enter Material Description:", placeholder="e.g., small pills for high blood sugar")
    submit_button = st.form_submit_button(label="Classify Material")

if submit_button and query:
    # STEP 1: Semantic Matching (Local) - Retrieve Top 3 Matches
    query_embedding = embed_model.encode(query, convert_to_tensor=True)
    cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
    
    # Get top 3 indices and their respective confidence scores
    top_results = torch.topk(cos_scores, k=3)
    top_indices = top_results.indices.tolist()
    top_scores = (top_results.values * 100).tolist()

    # The most favored match (Rank 1)
    match = df.iloc[top_indices[0]]
    confidence = top_scores[0]

    # --- MODIFIED SAFETY SWITCH ---
    THRESHOLD = 45 

    # Show warning if below threshold, but DO NOT stop the process
    if confidence < THRESHOLD:
        st.error(f"⚠️ **NON-CREDIBLE OUTPUT** (Confidence: {confidence:.1f}%)")
        st.warning("The semantic match for this item is very low. Results below are for reference only and may not align with Life Sciences compliance standards.")
    else:
        st.success(f"✅ **High Confidence Match** ({confidence:.1f}%)")

    # STEP 2: AI Reasoning (For the most favored match)
    prompt = f"""
    You are a Senior Trade Compliance Expert for a Global Life Sciences company.
    
    User Input: "{query}"
    Semantic Match in Database: {match['desc']}
    Initial HTS Recommendation: {match['hts']}
    
    Task:
    1. Confirm if the HTS code {match['hts']} is the most specific heading. 
    2. Explain the classification logic in 2-3 concise sentences using GRI 1 or GRI 3a.
    3. If the user input seems unrelated to the database match (low confidence), start your reasoning by stating this is a 'best-effort match'.
    """
    
    with st.spinner("AI analyzing compliance logic..."):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            response = model.generate_content(prompt)
            ai_reasoning = response.text
        except Exception as e:
            ai_reasoning = (f"The material '{query}' was matched to HTS {match['hts']} via semantic analysis. "
                            f"Logic: The item aligns closest with the definition of '{match['desc']}'.")

    # --- RESULTS DISPLAY ---
    st.subheader(f"Recommended HTS Code: :blue[{match['hts']}]")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🤖 AI Compliance Reasoning (Best Match)")
        st.info(ai_reasoning)
        st.caption(f"Top Match Confidence: {confidence:.1f}%")

    with col2:
        st.markdown("### 🔍 Alternative Suggestions")
        # Show alternative matches (Rank 2 and Rank 3)
        for i in range(1, len(top_indices)):
            alt_match = df.iloc[top_indices[i]]
            alt_conf = top_scores[i]
            
            with st.expander(f"Option {i+1}: HTS {alt_match['hts']} ({alt_conf:.1f}%)"):
                st.write(f"**Category:** {alt_match['cat']}")
                st.write(f"**Reference Description:** {alt_match['desc']}")

else:
    st.write("### Sector Knowledge Base (Sample Data)")
    st.dataframe(df[['hts', 'cat', 'desc']], use_container_width=True)

st.markdown("---")
st.caption("@Techylla Inc 2026. All Rights Reserved.")
