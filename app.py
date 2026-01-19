# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="Global Excellence Academy", layout="wide")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# 2. Security (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31"

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if not st.session_state['authenticated']:
        st.title("🔐 Software Activation")
        user_key = st.text_input("License Key", type="password")
        if st.button("Activate"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Invalid Key")
        return False
    return True

if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Clash-Free Multi-Class Timetable Generator")

    with st.sidebar:
        st.header("⚙️ Configuration")
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        periods_count = st.slider("Periods per Day", 1, 10, 8)
        start_time = st.time_input("School Start Time", datetime.strptime("08:00", "%H:%M"))
        period_duration = st.number_input("Period Duration (mins)", 30, 60, 45)

    col1, col2 = st.columns(2)
    with col1:
        classes_input = st.text_area("Classes", "Class 1, Class 2, Class 3, Class 4, Class 5, Class 6, Class 7, Class 8, Class 9, Class 10")
    with col2:
        teachers_input = st.text_area("Teachers", "Dr. Smith, Prof. Ahmed, Ms. Khan, Mr. Ali, Dr. Zehra, Mr. Junaid, Ms. Hina")
        subjects_input = st.text_area("Subjects", "Math, Physics, Chemistry, Biology, English, Urdu, Islamiyat")

    if st.button("🚀 Generate Optimized Timetable"):
        classes = [c.strip() for c in classes_input.split(",")]
        teachers = [t.strip() for t in teachers_input.split(",")]
        subjects = [s.strip() for s in subjects_input.split(",")]

        # Generate Time Slots
        time_slots = []
        curr_time = datetime.combine(datetime.today(), start_time)
        for i in range(periods_count):
            end_t = curr_time + timedelta(minutes=period_duration)
            time_slots.append(f"{curr_time.strftime('%I:%M %p')} - {end_t.strftime('%I:%M %p')}")
            curr_time = end_t

        # Logic to avoid Teacher Clashes
        master_schedule = {} # Keep track of teacher availability

        for student_class in classes:
            st.write(f"### 📋 Timetable: {student_class}")
            class_table = {}
            for day in days:
                daily_slots = []
                for p_idx in range(periods_count):
                    # Find a teacher who is free at this specific day and period
                    available_teachers = [t for t in teachers if (day, p_idx, t) not in master_schedule]
                    
                    if available_teachers:
                        chosen_teacher = random.choice(available_teachers)
                        chosen_subject = random.choice(subjects)
                        master_schedule[(day, p_idx, chosen_teacher)] = student_class
                        daily_slots.append(f"{chosen_teacher} \n ({chosen_subject})")
                    else:
                        daily_slots.append("NO TEACHER AVAILABLE")
                
                class_table[day] = daily_slots
            
            df = pd.DataFrame(class_table, index=time_slots)
            st.table(df)
            st.markdown("---")







