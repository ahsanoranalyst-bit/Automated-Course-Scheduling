import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# 1. Page Configuration
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
        user_key = st.text_input("Enter License Key", type="password")
        if st.button("Activate"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Invalid Key")
        return False
    return True

# Professional PDF Generation Function
def create_pdf(header_title, sub_title, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, header_title, ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, sub_title, ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 8)
    cols = ["Time Slot"] + list(df.columns)
    for col in cols:
        pdf.cell(30, 10, col, 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font("Arial", '', 7)
    for i in range(len(df)):
        pdf.cell(30, 10, str(df.index[i]), 1, 0, 'C')
        for col in df.columns:
            val = str(df[col][i]).replace('\n', ' ')
            pdf.cell(30, 10, val, 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Enterprise Resource Planning (ERP) - Timetable Module")

    with st.sidebar:
        st.header("⚙️ General Settings")
        days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("School Opening Time", datetime.strptime("08:00", "%H:%M"))
        period_duration = st.number_input("Period Duration (Mins)", 30, 60, 45)
        st.divider()
        st.header("☕ Break Management")
        after_period = st.number_input("Break After Period No.", 1, 10, 4)
        break_duration = st.number_input("Break Time (Mins)", 10, 60, 30)

    # Section-wise Tab Management
    st.markdown("### 🏛️ Faculty & Student Groups")
    tab1, tab2, tab3 = st.tabs(["👶 Primary Section", "🏫 Secondary Section", "🎓 College Section"])
    
    with tab1:
        c1, c2 = st.columns(2)
        pri_classes = c1.text_area("Primary Classes", "Grade 1, Grade 2, Grade 3")
        pri_teachers = c2.text_area("Primary Faculty", "Ms. Fatima, Ms. Zainab, Mr. Ali")
    with tab2:
        c1, c2 = st.columns(2)
        sec_classes = c1.text_area("Secondary Classes", "Grade 6, Grade 7, Grade 8")
        sec_teachers = c2.text_area("Secondary Faculty", "Mr. Sajid, Ms. Hina, Mr. Junaid")
    with tab3:
        c1, c2 = st.columns(2)
        coll_classes = c1.text_area("College Classes", "FSc Medical, FSc Engineering, A-Levels")
        coll_teachers = c2.text_area("College Faculty", "Dr. Smith, Prof. Ahmed, Dr. Zehra")

    subjects_input = st.text_input("Academic Subjects (Comma separated)", "Mathematics, Physics, English, Urdu, Science, Islamiyat")

    if st.button("🚀 Generate Master Timetable & PDF Reports"):
        # Organization Logic
        sections = [
            {"name": "Primary", "classes": [c.strip() for c in pri_classes.split(",")], "teachers": [t.strip() for t in pri_teachers.split(",")]},
            {"name": "Secondary", "classes": [c.strip() for c in sec_classes.split(",")], "teachers": [t.strip() for t in sec_teachers.split(",")]},
            {"name": "College", "classes": [c.strip() for c in coll_classes.split(",")], "teachers": [t.strip() for t in coll_teachers.split(",")]}
        ]
        subjects_list = [s.strip() for s in subjects_input.split(",")]
        
        master_data = {} # (day, time, teacher) -> class_subject
        all_teachers = []
        for s in sections: all_teachers.extend(s["teachers"])

        # Time Calculation Logic
        time_slots = []
        curr_time = datetime.combine(datetime.today(), school_start)
        for i in range(1, 10):
            start_t = curr_time.strftime('%I:%M%p')
            end_t_obj = curr_time + timedelta(minutes=period_duration)
            end_t = end_t_obj.strftime('%I:%M%p')
            time_slots.append({"label": f"Period {i}", "time": f"{start_t}-{end_t}", "is_break": False})
            curr_time = end_t_obj
            if i == after_period:
                b_end = curr_time + timedelta(minutes=break_duration)
                time_slots.append({"label": "BREAK", "time": f"{curr_time.strftime('%I:%M%p')}-{b_end.strftime('%I:%M%p')}", "is_break": True})
                curr_time = b_end

        # --- 1. Class-Wise Timetables ---
        st.header("📋 Student Class Timetables")
        for sec in sections:
            st.subheader(f"Section: {sec['name']}")
            for cls in sec["classes"]:
                class_schedule = {}
                for day in days:
                    day_slots = []
                    for slot in time_slots:
                        if slot["is_break"]:
                            day_slots.append("☕ BREAK")
                        else:
                            available = [t for t in sec["teachers"] if (day, slot["time"], t) not in master_data]
                            if available:
                                teacher = random.choice(available)
                                subj = random.choice(subjects_list)
                                master_data[(day, slot["time"], teacher)] = f"{cls} ({subj})"
                                day_slots.append(f"{teacher}\n({subj})")
                            else:
                                day_slots.append("❌ NO FACULTY")
                    class_schedule[day] = day_slots
                
                df_cls = pd.DataFrame(class_schedule, index=[s['time'] for s in time_slots])
                st.write(f"**Timetable for {cls}**")
                st.table(df_cls)
                pdf_bytes = create_pdf("Global Excellence Academy", f"Class Timetable: {cls}", df_cls)
                st.download_button(f"📥 Download {cls} PDF", pdf_bytes, f"{cls}_Schedule.pdf", "application/pdf")

        # --- 2. Teacher-Wise Timetables ---
        st.divider()
        st.header("👨‍🏫 Faculty Individual Duties")
        for teacher in all_teachers:
            teacher_schedule = {}
            for day in days:
                t_day_slots = []
                for slot in time_slots:
                    if slot["is_break"]:
                        t_day_slots.append("RECESSS")
                    else:
                        duty = master_data.get((day, slot["time"], teacher), "FREE PERIOD")
                        t_day_slots.append(duty)
                teacher_schedule[day] = t_day_slots
            
            df_t = pd.DataFrame(teacher_schedule, index=[s['time'] for s in time_slots])
            with st.expander(f"View Duty Chart for {teacher}"):
                st.table(df_t)
                pdf_t_bytes = create_pdf("Global Excellence Academy", f"Teacher Duty Chart: {teacher}", df_t)
                st.download_button(f"📥 Download {teacher}'s PDF", pdf_t_bytes, f"Teacher_{teacher}.pdf", "application/pdf")
