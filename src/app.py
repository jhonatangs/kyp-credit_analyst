import streamlit as st
import pandas as pd
import json
import time
import os
from dotenv import load_dotenv
from datetime import datetime

# Import backend logic
# Certifique-se de que src/main.py existe e a função está lá
try:
    from main import process_company_data
except ImportError:
    # Fallback para caso rode o streamlit da raiz ao invés de src/
    import sys

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from src.main import process_company_data

# Page Config
st.set_page_config(page_title="KYP Analyst AI", page_icon="🤖", layout="wide")

# Load environment variables explicitly
load_dotenv()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4248/4248387.png", width=50)
    st.title("KYP Control Panel")
    st.info("Automated Credit Analysis System for Duplicata Escritural.")

    st.markdown("---")
    st.markdown("### ⚙️ System Status")

    # --- CORREÇÃO AQUI: Checagem Segura da API Key ---
    api_key_status = False

    # 1. Tenta pegar do .env (Local)
    if os.environ.get("GROQ_API_KEY"):
        api_key_status = True

    # 2. Se não achar, tenta pegar do Streamlit Secrets (Nuvem) sem quebrar
    if not api_key_status:
        try:
            if st.secrets.get("GROQ_API_KEY"):
                api_key_status = True
        except Exception:
            pass  # Ignora se não existir secrets.toml

    if api_key_status:
        st.success("API Key Detected ✅")
    else:
        st.error("Missing GROQ_API_KEY ❌")
        st.caption("Please check your .env file")

# --- MAIN CONTENT ---
st.title("🤖 KYP: Credit Analysis Agent")
st.markdown("""
Scale your credit operations. Upload financial statements (JSON) 
and receive detailed risk analysis in seconds.
""")

st.markdown("---")

# 1. FILE UPLOAD
uploaded_files = st.file_uploader(
    "Upload Company JSON Files", type=["json"], accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📂 **{len(uploaded_files)} files identified.**")

    if st.button("🚀 Start Batch Analysis", type="primary"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Processing Loop
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # Load JSON into memory
                company_data = json.load(uploaded_file)
                company_name = company_data["company_info"]["name"]

                status_text.text(f"Analyzing: {company_name}...")

                # Call Backend
                analysis = process_company_data(company_data)
                results.append(analysis)

                # Update Progress
                progress_bar.progress((i + 1) / len(uploaded_files))

            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")

        time.sleep(0.5)
        status_text.text("✅ Processing Complete!")
        progress_bar.empty()

        # --- DISPLAY RESULTS ---
        if results:
            df = pd.DataFrame(results)

            # 2. KPI DASHBOARD
            st.markdown("### 📊 Operation Summary")
            col1, col2, col3 = st.columns(3)

            # Filtering based on English values
            approved_count = df[df["final_verdict"] == "APPROVE"].shape[0]
            avg_risk = df["risk_score"].mean()

            col1.metric("Processed Volume", f"{len(df)} Companies")
            col2.metric(
                "Approval Rate", f"{round((approved_count / len(df)) * 100, 1)}%"
            )
            col3.metric("Avg Risk Score", f"{int(avg_risk)}/100")

            # 3. DETAILED TABLE
            st.markdown("### 📝 Analysis Details")

            # Color logic for English Verdicts
            def color_verdict(val):
                if "APPROVE" in val:
                    return "background-color: #d4edda"  # Green
                elif "DENY" in val:
                    return "background-color: #f8d7da"  # Red
                else:
                    return "background-color: #fff3cd"  # Yellow/Orange (Conditions)

            st.dataframe(
                df.style.map(color_verdict, subset=["final_verdict"]),
                use_container_width=True,
            )

            # 4. DOWNLOAD CSV
            st.markdown("---")
            csv_data = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="📥 Download Consolidated Report (CSV)",
                data=csv_data,
                file_name=f"kyp_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="primary",
            )

else:
    st.info("👆 Waiting for file upload to start.")

# Footer
st.markdown("---")
st.caption("System developed for KYP Technical Challenge | Powered by Llama 3 & Groq")
