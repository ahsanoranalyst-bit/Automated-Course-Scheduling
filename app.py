import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF
import io

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

# PDF بنانے کا فنکشن
def create_pdf(school_name, class_name, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # اسکول کا نام
    pdf.cell(190, 10, school_name, ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    
    # کلاس کا نام
    pdf.cell(190, 10, f"Class Timetable: {class_name}", ln=True, align='C')
    pdf.ln(5)
    
    # ٹیبل کی سیٹنگ
    pdf.set_font("Arial", 'B', 8)
    # ہیڈر
    cols = ["Time"] + list(df.columns)
    for col in cols:
        pdf.cell(30, 10, col, 1, 0, 'C')
    pdf.ln()
    
    # ڈیٹا
    pdf.set_font("Arial", '', 7)
    for i in range(len(df)):
        pdf.cell(30, 10, str(df.index[i]), 1, 0, 'C')
        for col in df.columns:
            pdf.cell(30, 10, str(df[col][i]), 1, 0, 'C')
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Smart Timetable to PDF Generator")

    with st.sidebar:
        st.header("⚙️ Configuration")
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("Start Time", datetime.strptime("08:00", "%H:%M"))
        period_duration = st.number_input("Period (Mins)", 30, 60, 45)
        after_period = st.number_input("Break After Period", 1, 10, 4)
        break_duration = st.number_input("Break (Mins)", 10, 60, 30)

    # Sections
    tab1, tab2, tab3 = st.tabs(["Primary", "Secondary", "College"])
    with tab1:
        col1, col2 = st.columns(2)
        pri_classes = col1.text_area("Primary Classes", "Class 1, Class 2")
        pri_teachers = col2.text_area("Primary Teachers", "Ms. Fatima, Mr. Ali")
    with tab2:
        col1, col2 = st.columns(2)
        sec_classes = col1.text_area("Secondary Classes", "Class 6, Class 7")
        sec_teachers = col2.text_area("Secondary Teachers", "Mr. Sajid, Ms. Hina")
    with tab3:
        col1, col2 = st.columns(2)
        coll_classes = col1.text_area("College Classes", "FSc-1, A-Level")
        coll_teachers = col2.text_area("College Teachers", "Dr. Smith, Prof. Ahmed")

    subjects_input = st.text_input("Common Subjects", "Math, Physics, English, Urdu")

    if st.button("🚀 Generate PDF Timetables"):
        sections = [
            {"name": "Primary", "classes": [c.strip() for c in pri_classes.split(",")], "teachers": [t.strip() for t in pri_teachers.split(",")]},
            {"name": "Secondary", "classes": [c.strip() for c in sec_classes.split(",")], "teachers": [t.strip() for t in sec_teachers.split(",")]},
            {"name": "College", "classes": [c.strip() for c in coll_classes.split(",")], "teachers": [t.strip() for t in coll_teachers.split(",")]}
        ]
        
        master_schedule = {}
        # Time Logic
        time_slots = []
        curr_time = datetime.combine(datetime.today(), school_start)
        for i in range(1, 9):
            start_str = curr_time.strftime('%I:%M %p')
            end_t = curr_time + timedelta(minutes=period_duration)
            time_slots.append({"label": f"P{i}", "time": f"{start_str}-{end_t.strftime('%I:%M %p')}", "is_break": False})
            curr_time = end_t
            if i == after_period:
                b_end = curr_time + timedelta(minutes=break_duration)
                time_slots.append({"label": "BREAK", "time": f"{curr_time.strftime('%I:%M %p')}-{b_end.strftime('%I:%M %p')}", "is_break": True})
                curr_time = b_end

        for sec in sections:
            for cls in sec["classes"]:
                st.markdown(f"### 📋 Generating: {cls}")
                class_table = {}
                for day in days:
                    daily_slots = []
                    for slot in time_slots:
                        if slot["is_break"]:
                            daily_slots.append("BREAK")
                        else:
                            available = [t for t in sec["teachers"] if (day, slot["time"], t) not in master_schedule]
                            if available:
                                teacher = random.choice(available)
                                master_schedule[(day, slot["time"], teacher)] = cls
                                daily_slots.append(f"{teacher}")
                            else:
                                daily_slots.append("-")
                    class_table[day] = daily_slots
                
                df = pd.DataFrame(class_table, index=[s['time'] for s in time_slots])
                st.table(df)
                
                # PDF بٹن
                pdf_data = create_pdf("Global Excellence Academy", cls, df)
                st.download_button(label=f"📥 Download PDF for {cls}", data=pdf_data, file_name=f"{cls}_Timetable.pdf", mime="application/pdf")
