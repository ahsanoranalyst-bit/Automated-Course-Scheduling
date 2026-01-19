import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# 1. Page Config
st.set_page_config(page_title="Global Excellence Academy ERP", layout="wide")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# 2. Security (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31"

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if not st.session_state['authenticated']:
        st.title("🔐 Software Activation")
        user_key = st.text_input("Enter License Master Key", type="password")
        if st.button("Activate System"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Invalid Key")
        return False
    return True

# 3. PDF Generator
def create_pdf(header, sub, df):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, str(header), ln=True, align='C')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, str(sub), ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 8)
        cols = ["Time Slot"] + list(df.columns)
        w = 190 / len(cols)
        for col in cols: pdf.cell(w, 10, str(col), 1, 0, 'C')
        pdf.ln()
        pdf.set_font("Arial", '', 7)
        for i in range(len(df)):
            pdf.cell(w, 10, str(df.index[i]), 1, 0, 'C')
            for col in df.columns:
                clean_text = str(df[col][i]).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(w, 10, clean_text, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"PDF Error: {e}")
        return None

if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Smart Academic Scheduling with Auto-Closing Logic")

    with st.sidebar:
        st.header("⚙️ Timing Settings")
        days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        st.divider()
        school_start = st.time_input("School Opening Time", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("School Closing Time", datetime.strptime("14:00", "%H:%M"))
        period_duration = st.number_input("Period Duration (Mins)", 10, 120, 45)
        
        st.divider()
        after_period = st.number_input("Break After Period No.", 1, 10, 4)
        break_duration = st.number_input("Break Duration (Mins)", 10, 60, 30)

    # Data Tabs
    tab1, tab2, tab3 = st.tabs(["👶 Primary", "🏫 Secondary", "🎓 College"])
    with tab1:
        c1, c2 = st.columns(2)
        pri_classes = c1.text_area("Primary Classes", "Grade 1, Grade 2")
        pri_teachers = c2.text_area("Primary Faculty", "Ms. Fatima, Mr. Ali")
    with tab2:
        c1, c2 = st.columns(2)
        sec_classes = c1.text_area("Secondary Classes", "Grade 6, Grade 7")
        sec_teachers = c2.text_area("Secondary Faculty", "Mr. Sajid, Ms. Hina")
    with tab3:
        c1, c2 = st.columns(2)
        coll_classes = c1.text_area("College Classes", "FSc, A-Levels")
        coll_teachers = c2.text_area("College Faculty", "Dr. Smith, Prof. Ahmed")

    subjects_input = st.text_input("Academic Subjects", "Math, Physics, English, Urdu, Science")

    if st.button("🚀 Generate Optimized Timetables"):
        sections = [
            {"name": "Primary", "classes": [c.strip() for c in pri_classes.split(",")], "teachers": [t.strip() for t in pri_teachers.split(",")]},
            {"name": "Secondary", "classes": [c.strip() for c in sec_classes.split(",")], "teachers": [t.strip() for t in sec_teachers.split(",")]},
            {"name": "College", "classes": [c.strip() for c in coll_classes.split(",")], "teachers": [t.strip() for t in coll_teachers.split(",")]}
        ]
        
        master_registry = {}
        all_faculty = []
        for s in sections: all_faculty.extend(s["teachers"])

        # --- SMART TIME SLOTS CALCULATION ---
        time_slots = []
        curr = datetime.combine(datetime.today(), school_start)
        closing = datetime.combine(datetime.today(), school_end)
        
        p_num = 1
        while True:
            # Check if next period fits before closing
            potential_end = curr + timedelta(minutes=period_duration)
            if potential_end > closing:
                break
            
            slot_range = f"{curr.strftime('%I:%M %p')}-{potential_end.strftime('%I:%M %p')}"
            time_slots.append({"label": f"Period {p_num}", "time": slot_range, "is_break": False})
            curr = potential_end
            
            # Check for Break
            if p_num == after_period:
                potential_break_end = curr + timedelta(minutes=break_duration)
                if potential_break_end <= closing:
                    break_range = f"{curr.strftime('%I:%M %p')}-{potential_break_end.strftime('%I:%M %p')}"
                    time_slots.append({"label": "BREAK", "time": break_range, "is_break": True})
                    curr = potential_break_end
            p_num += 1

        if not time_slots:
            st.error("Error: School timing is too short for even one period. Please adjust start/end times.")
        else:
            # 1. Class Timetables
            st.header("📋 Student Class Timetables")
            for sec in sections:
                for cls in sec["classes"]:
                    cls_sched = {}
                    for day in days:
                        day_plan = []
                        for slot in time_slots:
                            if slot["is_break"]: day_plan.append("☕ BREAK")
                            else:
                                available = [t for t in sec["teachers"] if (day, slot["time"], t) not in master_registry]
                                if available:
                                    t_assigned = random.choice(available)
                                    s_assigned = random.choice(subjects_input.split(","))
                                    master_registry[(day, slot["time"], t_assigned)] = f"{cls} ({s_assigned.strip()})"
                                    day_plan.append(f"{t_assigned}\n({s_assigned.strip()})")
                                else: day_plan.append("❌ NO STAFF")
                        cls_sched[day] = day_plan
                    
                    df_cls = pd.DataFrame(cls_sched, index=[s['time'] for s in time_slots])
                    st.write(f"**Class: {cls}**")
                    st.table(df_cls)
                    pdf_c = create_pdf("Global Excellence Academy", f"Class Schedule: {cls}", df_cls)
                    if pdf_c: st.download_button(f"📥 Download {cls} PDF", pdf_c, f"{cls}_Schedule.pdf")

            # 2. Teacher Duty Charts
            st.divider()
            st.header("👨‍🏫 Faculty Personal Duty Charts")
            for teacher in all_faculty:
                t_sched = {}
                for day in days:
                    t_plan = []
                    for slot in time_slots:
                        if slot["is_break"]: t_plan.append("RECESSS")
                        else: t_plan.append(master_registry.get((day, slot["time"], teacher), "FREE"))
                    t_sched[day] = t_plan
                
                df_t = pd.DataFrame(t_sched, index=[s['time'] for s in time_slots])
                with st.expander(f"View Duty Chart: {teacher}"):
                    st.table(df_t)
                    pdf_t = create_pdf("Global Excellence Academy", f"Teacher Duty Chart: {teacher}", df_t)
                    if pdf_t: st.download_button(f"📥 Download {teacher} PDF", pdf_t, f"Teacher_{teacher}.pdf")
