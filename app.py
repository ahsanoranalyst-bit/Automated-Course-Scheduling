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
        user_key = st.text_input("Enter License Key", type="password")
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
    st.subheader("Smart Section-Based Timetable System")

    with st.sidebar:
        st.header("⚙️ Settings")
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("Start Time", datetime.strptime("08:00", "%H:%M"))
        period_duration = st.number_input("Period (Mins)", 30, 60, 45)
        after_period = st.number_input("Break After Period", 1, 10, 4)
        break_duration = st.number_input("Break (Mins)", 10, 60, 30)

    # --- Section-wise Teacher and Class Inputs ---
    st.markdown("### 🏛️ Section Management")
    tab1, tab2, tab3 = st.tabs(["👶 Primary Section", "🏫 Secondary Section", "🎓 College Section"])

    with tab1:
        col1, col2 = st.columns(2)
        pri_classes = col1.text_area("Primary Classes", "Class 1, Class 2, Class 3, Class 4, Class 5")
        pri_teachers = col2.text_area("Primary Teachers", "Ms. Fatima, Ms. Zainab, Mr. Ali")
    
    with tab2:
        col1, col2 = st.columns(2)
        sec_classes = col1.text_area("Secondary Classes", "Class 6, Class 7, Class 8, Class 9, Class 10")
        sec_teachers = col2.text_area("Secondary Teachers", "Mr. Sajid, Ms. Hina, Mr. Junaid")

    with tab3:
        col1, col2 = st.columns(2)
        coll_classes = col1.text_area("College Classes", "FSc Part 1, FSc Part 2, A-Levels")
        coll_teachers = col2.text_area("College/Expert Teachers", "Dr. Smith, Prof. Ahmed, Dr. Zehra")

    subjects_input = st.text_input("Common Subjects (Comma separated)", "Math, Physics, English, Urdu, Science, Biology")

    if st.button("🚀 Generate Optimized Section-Wise Timetable"):
        # Process Inputs
        sections = [
            {"name": "Primary", "classes": [c.strip() for c in pri_classes.split(",")], "teachers": [t.strip() for t in pri_teachers.split(",")]},
            {"name": "Secondary", "classes": [c.strip() for c in sec_classes.split(",")], "teachers": [t.strip() for t in sec_teachers.split(",")]},
            {"name": "College", "classes": [c.strip() for c in coll_classes.split(",")], "teachers": [t.strip() for t in coll_teachers.split(",")]}
        ]
        subjects = [s.strip() for s in subjects_input.split(",")]

        # Time Calculation
        time_slots = []
        curr_time = datetime.combine(datetime.today(), school_start)
        for i in range(1, 9): # 8 Periods
            start_str = curr_time.strftime('%I:%M %p')
            end_t = curr_time + timedelta(minutes=period_duration)
            time_slots.append({"label": f"Period {i}", "time": f"{start_str}-{end_t.strftime('%I:%M %p')}", "is_break": False})
            curr_time = end_t
            if i == after_period:
                b_end = curr_time + timedelta(minutes=break_duration)
                time_slots.append({"label": "BREAK", "time": f"{curr_time.strftime('%I:%M %p')}-{b_end.strftime('%I:%M %p')}", "is_break": True})
                curr_time = b_end

        master_schedule = {} # To avoid clashes

        for sec in sections:
            st.markdown(f"## 🏁 {sec['name']} Section")
            for cls in sec["classes"]:
                st.write(f"### 📋 Timetable: {cls}")
                class_table = {}
                for day in days:
                    daily_slots = []
                    for slot in time_slots:
                        if slot["is_break"]:
                            daily_slots.append("☕ BREAK")
                        else:
                            # Use ONLY section-specific teachers
                            available = [t for t in sec["teachers"] if (day, slot["time"], t) not in master_schedule]
                            if available:
                                teacher = random.choice(available)
                                master_schedule[(day, slot["time"], teacher)] = cls
                                daily_slots.append(f"{teacher}\n({random.choice(subjects)})")
                            else:
                                daily_slots.append("❌ NO TEACHER")
                    class_table[day] = daily_slots
                
                df = pd.DataFrame(class_table, index=[f"{s['label']} ({s['time']})" for s in time_slots])
                st.table(df)
                csv = df.to_csv().encode('utf-8')
                st.download_button(f"📥 Download {cls} PDF/Excel", csv, f"{cls}.csv", "text/csv")







