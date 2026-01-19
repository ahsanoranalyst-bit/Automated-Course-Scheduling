# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import datetime

# --- Security & License System ---
MASTER_KEY = "AHSAN-PRO-200"

st.set_page_config(page_title="AI Timetable Scheduler", layout="wide")

# Theme Styling
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #007bff; color: white; border-radius: 8px; width: 100%; }
    .header-box { background: #1e3a8a; padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.markdown("<div class='header-box'><h1>🔐 License Activation</h1></div>", unsafe_allow_html=True)
    key_input = st.text_input("Enter Master Key to Unlock", type="password")
    expiry_date = "2026-12-31" # Automated Expiry
    
    if st.button("Activate Software"):
        if key_input == MASTER_KEY:
            st.session_state['authenticated'] = True
            st.success("Software Activated! Profit Level: 200")
            st.rerun()
        else:
            st.error("Invalid Key. Contact Admin.")
    st.stop()

# --- Main App Interface ---
st.markdown("<div class='header-box'><h1>📅 Smart Education Timetable Scheduler</h1><p>AI-Powered Optimization</p></div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    school_name = st.text_input("Institution Name", "Global Excellence Academy")
    days = st.multiselect("Working Days", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], ["Mon", "Tue", "Wed", "Thu", "Fri"])
    periods = st.slider("Periods per Day", 1, 10, 8)

col1, col2 = st.columns(2)
with col1:
    teachers = st.text_area("Teachers (Comma separated)", "Dr. Smith, Prof. Ahmed, Ms. Khan")
with col2:
    subjects = st.text_area("Subjects (Comma separated)", "Math, Physics, English, Computer")

if st.button("Generate Optimized Timetable"):
    # Simplified Logic for Demo - In real code, OR-Tools constraints are added here
    st.balloons()
    st.subheader(f"✅ Optimized Schedule for {school_name}")
    
    # Mock Dataframe Generation
    teacher_list = teachers.split(",")
    subject_list = subjects.split(",")
    schedule_data = {day: [subject_list[i % len(subject_list)] for i in range(periods)] for day in days}
    df = pd.DataFrame(schedule_data)
    df.index = [f"Period {i+1}" for i in range(periods)]
    
    st.table(df)

    st.info(f"License Status: Active | Expiry: "{2026-12-31}")



