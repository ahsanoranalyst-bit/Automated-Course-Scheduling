# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# 1. Page Config & Professional Branding
st.set_page_config(page_title="Global Excellence Academy", layout="wide")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# 2. Security & License (Profit Level 200)
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
    st.subheader("Professional Timetable Management System")

    # --- Sidebar for School Controls ---
    with st.sidebar:
        st.header("⚙️ School Timing Settings")
        
        days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        # اسکول شروع اور ختم ہونے کا وقت
        school_start = st.time_input("School Opening Time", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("School Closing Time (Target)", datetime.strptime("14:00", "%H:%M"))
        
        # پیریڈ کا دورانیہ
        period_duration = st.number_input("Duration of one Period (Minutes)", min_value=10, max_value=120, value=45)
        
        st.divider()
        st.header("☕ Break Settings")
        after_period = st.number_input("Break After Period No.", 1, 10, 4)
        break_duration = st.number_input("Break Duration (Minutes)", 10, 60, 30)

    # --- Data Input ---
    col1, col2 = st.columns(2)
    with col1:
        classes_input = st.text_area("Enter Classes (Comma separated)", "Class 1, Class 2, Class 3, Class 4, Class 5")
    with col2:
        teachers_input = st.text_area("Enter Teachers", "Dr. Smith, Prof. Ahmed, Ms. Khan, Mr. Ali, Dr. Zehra")
        subjects_input = st.text_area("Enter Subjects", "Math, Physics, Chemistry, Biology, English")

    if st.button("🚀 Generate Optimized Timetable"):
        classes = [c.strip() for c in classes_input.split(",")]
        teachers = [t.strip() for t in teachers_input.split(",")]
        subjects = [s.strip() for s in subjects_input.split(",")]

        # --- Time Logic Calculation ---
        time_slots = []
        curr_time = datetime.combine(datetime.today(), school_start)
        closing_time = datetime.combine(datetime.today(), school_end)
        
        p_idx = 1
        while curr_time + timedelta(minutes=period_duration) <= closing_time:
            # Period Time
            start_str = curr_time.strftime('%I:%M %p')
            end_t = curr_time + timedelta(minutes=period_duration)
            end_str = end_t.strftime('%I:%M %p')
            
            time_slots.append({"label": f"Period {p_idx}", "time": f"{start_str} - {end_str}", "is_break": False})
            curr_time = end_t
            
            # Insert Break
            if p_idx == after_period:
                b_start = curr_time.strftime('%I:%M %p')
                b_end_t = curr_time + timedelta(minutes=break_duration)
                b_end_str = b_end_t.strftime('%I:%M %p')
                time_slots.append({"label": "RECESSS / BREAK", "time": f"{b_start} - {b_end_str}", "is_break": True})
                curr_time = b_end_t
            
            p_idx += 1

        # --- Generation & Clash Prevention ---
        master_schedule = {} 

        for student_class in classes:
            st.write(f"### 📋 Timetable for: {student_class}")
            class_table = {}
            
            for day in days:
                daily_slots = []
                period_num = 0
                
                for slot in time_slots:
                    if slot["is_break"]:
                        daily_slots.append("☕ BREAK")
                    else:
                        # Teacher Clash Check
                        available_teachers = [t for t in teachers if (day, slot["time"], t) not in master_schedule]
                        
                        if available_teachers:
                            t_name = random.choice(available_teachers)
                            s_name = random.choice(subjects)
                            master_schedule[(day, slot["time"], t_name)] = student_class
                            daily_slots.append(f"{t_name} \n ({s_name})")
                        else:
                            daily_slots.append("❌ NO TEACHER")
                        period_num += 1
                
                class_table[day] = daily_slots
            
            # DataFrame display
            row_labels = [f"{s['label']} \n ({s['time']})" for s in time_slots]
            df = pd.DataFrame(class_table, index=row_labels)
            st.table(df)
            st.markdown("---")







