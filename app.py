# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import random
from datetime import datetime

# 1. Page Configuration & Design
st.set_page_config(page_title="Global Excellence Academy", layout="wide")

# CSS to hide Streamlit branding for a professional look
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. Security & License Configuration (Profit Level 200)
MASTER_KEY = "AhsanPro200" # Your secure key
EXPIRY_DATE = "2026-12-31" # Your expiry date

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if not st.session_state['authenticated']:
        st.title("🔐 Software Activation")
        st.info("Please enter your license key to access the Timetable Management System.")
        
        user_key = st.text_input("License Key", type="password", help="Enter the key provided by the administrator.")
        
        if st.button("Activate License"):
            if user_key == MASTER_KEY:
                # Check if the software has expired
                current_date = datetime.now().date()
                expiry = datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date()
                
                if current_date <= expiry:
                    st.session_state['authenticated'] = True
                    st.success("License Activated Successfully!")
                    st.rerun()
                else:
                    st.error(f"This license expired on {EXPIRY_DATE}. Please contact support for renewal.")
            else:
                st.error("Invalid License Key. Please try again.")
        return False
    return True

# 3. Main Application Logic
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Advanced Timetable Management System")
    st.write("Management for Schools, FSc Colleges, and O/A-Levels.")

    # Sidebar Settings
    with st.sidebar:
        st.header("⚙️ Configuration")
        days = st.multiselect("Select Working Days", 
                             ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], 
                             ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        periods = st.slider("Periods Per Day", 1, 12, 8)
        
        st.divider()
        st.write(f"**License Status:** Active ✅")
        st.write(f"**Valid Until:** {EXPIRY_DATE}")

    # Data Input Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎓 Classes Setup")
        classes_input = st.text_area("List your Classes (comma separated):", 
            "Class 1, Class 2, Class 3, Class 4, Class 5, Class 6, Class 7, Class 8, Class 9, Class 10, FSc Pre-Engineering, FSc Pre-Medical, A-Level, O-Level")
    
    with col2:
        st.markdown("### 👨‍🏫 Faculty & Subjects")
        teachers_input = st.text_area("Teachers Names:", "Dr. Smith, Prof. Ahmed, Ms. Khan, Mr. Ali, Dr. Zehra")
        subjects_input = st.text_area("Subjects List:", "Mathematics, Physics, Chemistry, Biology, English, Urdu, Economics, Business Studies")

    # Generate Button
    if st.button("🚀 Generate Optimized Timetables"):
        classes_list = [c.strip() for c in classes_input.split(",")]
        teachers_list = [t.strip() for t in teachers_input.split(",")]
        subjects_list = [s.strip() for s in subjects_input.split(",")]
        
        if not teachers_list or not subjects_list:
            st.warning("Please enter at least one teacher and one subject.")
        else:
            for student_class in classes_list:
                st.markdown(f"## 📋 Timetable for: **{student_class}**")
                
                # Logic to build the grid
                timetable_data = {}
                for day in days:
                    daily_slots = []
                    for p in range(periods):
                        teacher = random.choice(teachers_list)
                        subject = random.choice(subjects_list)
                        daily_slots.append(f"{teacher} \n ({subject})")
                    timetable_data[day] = daily_slots
                    
                # Creating a clean Table
                df = pd.DataFrame(timetable_data, index=[f"Period {i+1}" for i in range(periods)])
                st.table(df)
                st.markdown("---")







