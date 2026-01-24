import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF
import requests
from streamlit_gsheets import GSheetsConnection

# --- NEW: GOOGLE SHEETS CONNECTION & DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)
gsheet_url = "https://docs.google.com/spreadsheets/d/1z5-bAxtwbaIbc513okBAggN1tdgIz-dpXioIm0SjXuw/edit?usp=sharing"

if 'gsheet_data' not in st.session_state:
    try:
        # Loading data into session state to keep it accessible
        st.session_state.gsheet_data = conn.read(spreadsheet=gsheet_url)
    except:
        st.session_state.gsheet_data = pd.DataFrame()

# 1. Page Configuration
st.set_page_config(page_title="School ERP Pro", layout="wide")

# 2. Security (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31"

def check_license():
    if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error(" LICENSE EXPIRED!")
        return False
    if not st.session_state['authenticated']:
        st.title(" Enterprise Software Activation")
        user_key = st.text_input("Enter Activation Key:", type="password")
        if st.button("Activate"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Invalid Key")
        return False
    return True

# 3. PDF Generator
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
                val = str(df[col].iloc[i]).encode('ascii', 'ignore').decode('ascii')
                pdf.cell(w, 10, val, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# 4. Main ERP Logic
if check_license():
    with st.sidebar:
        st.header(" School Setup")
        custom_school_name = st.text_input("Enter School Name:", "Global Excellence Academy")
        st.divider()
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_t = st.time_input("Open", datetime.strptime("08:00", "%H:%M"))
        end_t = st.time_input("Close", datetime.strptime("14:00", "%H:%M"))
        p_mins = st.number_input("Period Duration", 10, 120, 40)
        brk_after = st.number_input("Break After Period", 1, 10, 4)
        brk_mins = st.number_input("Break Mins", 10, 60, 30)
        
        # --- SIDEBAR BUTTONS ---
        st.divider()
        if st.button("Save Configuration", use_container_width=True, type="primary"):
            # Prepare data for both sync methods
            log_time = datetime.now().strftime("%Y-%m-%d %H
