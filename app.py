import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. FIREBASE INITIALIZATION ---
if not firebase_admin._apps:
    # Ensure your 'serviceAccountKey.json' is in the same folder
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Init Error: {e}")

db = firestore.client()

# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Automated Course Scheduling Optimizer", layout="wide")

# --- 3. SECURITY & SESSION STATE ---
MASTER_KEY = "Ahsan123"
EXPIRY_DATE = "2030-12-31"

if 'user_data' not in st.session_state:
    st.session_state.user_data = {}

# --- 4. UNIVERSAL LOAD FUNCTION ---
def load_from_cloud():
    try:
        doc_ref = db.collection("registrations").document(MASTER_KEY)
        doc = doc_ref.get()
        if doc.exists:
            st.session_state.user_data = doc.to_dict()
            return True
    except Exception as e:
        st.error(f"Load Error: {e}")
    return False

# --- 5. UNIVERSAL SAVE FUNCTION ---
def sync_to_cloud(data_dict):
    try:
        doc_ref = db.collection("registrations").document(MASTER_KEY)
        doc_ref.set(data_dict, merge=True)
        st.session_state.user_data.update(data_dict)
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

def get_old_val(key, default):
    return st.session_state.user_data.get(key, default)

# --- 6. LICENSE CHECK ---
def check_license():
    if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error(" LICENSE EXPIRED!")
        return False
    if not st.session_state['authenticated']:
        st.title(" Automated Course Scheduling Optimizer Activation")
        user_key = st.text_input("Enter Activation Key:", type="password")
        if st.button("Activate"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                load_from_cloud() # Load data immediately upon successful login
                st.rerun()
            else: st.error("Invalid Key")
        return False
    return True

# --- 7. PDF GENERATOR ---
def create_pdf(school_name, header, sub, df):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(190, 15, str(school_name).upper(), ln=True, align='C')
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, str(header), ln=True, align='C')
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(190, 8, str(sub), ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 9)
        cols = ["Time Slot"] + list(df.columns)
        w = 190 / len(cols)
        for col in cols: pdf.cell(w, 10, str(col), 1, 0, 'C')
        pdf.ln()
        pdf.set_font("Arial", '', 8)
        for i in range(len(df)):
            pdf.cell(w, 10, str(df.index[i]), 1, 0, 'C')
            for col in df.columns:
                val = str(df[col][i]).encode('ascii', 'ignore').decode('ascii')
                pdf.cell(w, 10, val, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# --- 8. MAIN ERP LOGIC ---
if check_license():
    with st.sidebar:
        st.header(" School Setup")
        custom_school_name = st.text_input("Enter School Name:", get_old_val("school_name", "Global Excellence Academy"))
        st.divider()
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], get_old_val("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]))
        
        # Safe Time Parsing
        def get_stored_time(key, default_str):
            time_str = get_old_val(key, default_str)
            return datetime.strptime(time_str, "%H:%M")

        start_t = st.time_input("Open", get_stored_time("start_t", "08:00"))
        end_t = st.time_input("Close", get_stored_time("end_t", "14:00"))
        p_mins = st.number_input("Period Duration", 10, 120, get_old_val("p_mins", 40))
        brk_after = st.number_input("Break After Period", 1, 10, get_old_val("brk_after", 4))
        brk_mins = st.number_input("Break Mins", 10, 60, get_old_val("brk_mins", 30))
        
        st.divider()
        # SAVE BUTTON
        if st.button("Save Configuration", use_container_width=True, type="primary"):
            save_data = {
                "school_name": custom_school_name,
                "days": days,
                "start_t": start_t.strftime("%H:%M"),
                "end_t": end_t.strftime("%H:%M"),
                "p_mins": p_mins,
                "brk_after": brk_after,
                "brk_mins": brk_mins,
                "p_c_data": p_c_df.to_dict('records'),
                "p_t_data": p_t_df.to_dict('records'),
                "s_c_data": s_c_df.to_dict('records'),
                "s_t_data": s_t_df.to_dict('records'),
                "c_c_data": c_c_df.to_dict('records'),
                "c_t_data": c_t_df.to_dict('records')
            }
            if sync_to_cloud(save_data):
                st.sidebar.success("✅ Data Synced to Cloud!")
            
        if st.button("Logout", use_container_width=True):
            st.session_state['authenticated'] = False
            st.session_state.user_data = {}
            st.rerun()

    st.title(f" {custom_school_name}")
    
    # Registration Tabs with Dynamic Loading
    tab1, tab2, tab3 = st.tabs(["Primary Registration", "Secondary Registration", "College Registration"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        p_c_df = col1.data_editor(pd.DataFrame(get_old_val("p_c_data", [{"Class": "Grade 1", "Sections": 1}])), num_rows="dynamic", key="p_c")
        p_t_df = col2.data_editor(pd.DataFrame(get_old_val("p_t_data", [{"Name": "", "Subject": ""}] * 5)), num_rows="dynamic", key="p_t")

    with tab2:
        col1, col2 = st.columns([1, 2])
        s_c_df = col1.data_editor(pd.DataFrame(get_old_val("s_c_data", [{"Class": "Grade 9", "Sections": 1}])), num_rows="dynamic", key="s_c")
        s_t_df = col2.data_editor(pd.DataFrame(get_old_val("s_t_data", [{"Name": "", "Subject": ""}] * 5)), num_rows="dynamic", key="s_t")

    with tab3:
        col1, col2 = st.columns([1, 2])
        c_c_df = col1.data_editor(pd.DataFrame(get_old_val("c_c_data", [{"Class": "FSc-1", "Sections": 1}])), num_rows="dynamic", key="c_c")
        c_t_df = col2.data_editor(pd.DataFrame(get_old_val("c_t_data", [{"Name": "", "Subject": ""}] * 5)), num_rows="dynamic", key="c_t")

    # The Run Analysis logic remains identical to your original code
    if st.button(" Run Analysis"):
        # ... (Same logic as provided in your original script)
        st.info("Analysis Running...")
