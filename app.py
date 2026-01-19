import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# 1. Page Configuration & Professional UI
st.set_page_config(page_title="Global Excellence Academy - ERP", layout="wide")
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button { background-color: #007bff; color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Security & License Logic (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31"

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if not st.session_state['authenticated']:
        st.title("🔐 Enterprise Software Activation")
        st.info("Global Excellence Academy - Timetable Management System")
        user_key = st.text_input("Please enter your Master License Key:", type="password")
        if st.button("Activate System"):
            if user_key == MASTER_KEY:
                current_date = datetime.now().date()
                expiry = datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date()
                if current_date <= expiry:
                    st.session_state['authenticated'] = True
                    st.success("License Verified! Welcome, Administrator.")
                    st.rerun()
                else:
                    st.error("License Expired. Please contact your provider for renewal.")
            else:
                st.error("Invalid License Key. Access Denied.")
        return False
    return True

# 3. PDF Generator Function (Optimized for Printing)
def create_pdf(header_title, sub_title, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, header_title, ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, sub_title, ln=True, align='C')
    pdf.ln(10)
    
    # Header
    pdf.set_font("Arial", 'B', 9)
    column_width = 190 / (len(df.columns) + 1)
    pdf.cell(column_width, 10, "Time/Period", 1, 0, 'C')
    for col in df.columns:
        pdf.cell(column_width, 10, col, 1, 0, 'C')
    pdf.ln()
    
    # Body
    pdf.set_font("Arial", '', 8)
    for i in range(len(df)):
        pdf.cell(column_width, 10, str(df.index[i]), 1, 0, 'C')
        for col in df.columns:
            content = str(df[col][i]).replace('\n', ' ')
            pdf.cell(column_width, 10, content, 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# 4. Main Application
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Professional Academic Scheduling System (ERP)")

    # Sidebar: Comprehensive Controls
    with st.sidebar:
        st.header("⚙️ System Configuration")
        days = st.multiselect("Select Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        st.divider()
        st.subheader("⏰ Timing Control")
        school_start = st.time_input("School Opening Time", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("School Closing Time", datetime.strptime("14:00", "%H:%M"))
        period_duration = st.number_input("One Period Duration (Mins)", 10, 120, 45)
        
        st.divider()
        st.subheader("☕ Break Management")
        after_period = st.number_input("Lunch/Break After Period No.", 1, 10, 4)
        break_duration = st.number_input("Break Length (Mins)", 10, 60, 30)

    # Main Panel: Section Wise Inputs
    st.markdown("### 👨‍🏫 Faculty & Section Management")
    tab1, tab2, tab3 = st.tabs(["👶 Primary Section", "🏫 Secondary Section", "🎓 College Section"])
    
    with tab1:
        col1, col2 = st.columns(2)
        pri_classes = col1.text_area("Primary Classes", "Grade 1, Grade 2, Grade 3, Grade 4, Grade 5")
        pri_teachers = col2.text_area("Primary Faculty", "Ms. Fatima, Ms. Zainab, Mr. Ali, Ms. Sara")
    
    with tab2:
        col1, col2 = st.columns(2)
        sec_classes = col1.text_area("Secondary Classes", "Grade 6, Grade 7, Grade 8, Grade 9, Grade 10")
        sec_teachers = col2.text_area("Secondary Faculty", "Mr. Sajid, Ms. Hina, Mr. Junaid, Mr. Hassan")
    
    with tab3:
        col1, col2 = st.columns(2)
        coll_classes = col1.text_area("College Classes", "FSc Pre-Med, FSc Pre-Eng, A-Levels, O-Levels")
        coll_teachers = col2.text_area("College/Specialist Faculty", "Dr. Smith, Prof. Ahmed, Dr. Zehra, Prof. Khan")

    common_subjects = st.text_input("List of Academic Subjects (Comma Separated)", "Mathematics, Physics, Chemistry, English, Urdu, Islamiyat, Science")

    if st.button("🚀 Generate Optimized Master Schedules"):
        # Formatting Inputs
        sections = [
            {"name": "Primary", "classes": [c.strip() for c in pri_classes.split(",")], "teachers": [t.strip() for t in pri_teachers.split(",")]},
            {"name": "Secondary", "classes": [c.strip() for c in sec_classes.split(",")], "teachers": [t.strip() for t in sec_teachers.split(",")]},
            {"name": "College", "classes": [c.strip() for c in coll_classes.split(",")], "teachers": [t.strip() for t in coll_teachers.split(",")]}
        ]
        subjects = [s.strip() for s in common_subjects.split(",")]
        
        # Generation Logic Setup
        master_registry = {} # Tracking: (day, time_slot, teacher)
        time_slots = []
        curr_time = datetime.combine(datetime.today(), school_start)
        closing = datetime.combine(datetime.today(), school_end)
        
        p_count = 1
        while curr_time + timedelta(minutes=period_duration) <= closing:
            start_s = curr_time.strftime('%I:%M %p')
            end_t = curr_time + timedelta(minutes=period_duration)
            time_slots.append({"label": f"Period {p_count}", "time": f"{start_s}-{end_t.strftime('%I:%M %p')}", "is_break": False})
            curr_time = end_t
            if p_count == after_period:
                b_end = curr_time + timedelta(minutes=break_duration)
                time_slots.append({"label": "BREAK", "time": f"{curr_time.strftime('%I:%M %p')}-{b_end.strftime('%I:%M %p')}", "is_break": True})
                curr_time = b_end
            p_count += 1

        # --- Generate Class Timetables ---
        st.header("📋 Class-Wise Schedules")
        for sec in sections:
            st.subheader(f"Section: {sec['name']}")
            for cls in sec["classes"]:
                cls_data = {}
                for day in days:
                    day_plan = []
                    for slot in time_slots:
                        if slot["is_break"]: day_plan.append("☕ BREAK")
                        else:
                            free_teachers = [t for t in sec["teachers"] if (day, slot["time"], t) not in master_registry]
                            if free_teachers:
                                t_assigned = random.choice(free_teachers)
                                s_assigned = random.choice(subjects)
                                master_registry[(day, slot["time"], t_assigned)] = f"{cls} ({s_assigned})"
                                day_plan.append(f"{t_assigned}\n({s_assigned})")
                            else: day_plan.append("❌ NO STAFF")
                    cls_data[day] = day_plan
                
                df_cls = pd.DataFrame(cls_data, index=[s['time'] for s in time_slots])
                st.write(f"**Timetable for {cls}**")
                st.table(df_cls)
                pdf_bytes = create_pdf("Global Excellence Academy", f"Class Schedule: {cls}", df_cls)
                st.download_button(f"📥 Download {cls} PDF", pdf_bytes, f"{cls}_Schedule.pdf", "application/pdf")

        # --- Generate Teacher Duty Charts ---
        st.divider()
        st.header("👨‍🏫 Faculty Personal Duty Charts")
        all_faculty = []
        for s in sections: all_faculty.extend(s["teachers"])
        
        for teacher in all_faculty:
            t_data = {}
            for day in days:
                t_plan = []
                for slot in time_slots:
                    if slot["is_break"]: t_plan.append("RECESSS")
                    else:
                        assignment = master_registry.get((day, slot["time"], teacher), "FREE PERIOD")
                        t_plan.append(assignment)
                t_data[day] = t_plan
            
            df_t = pd.DataFrame(t_data, index=[s['time'] for s in time_slots])
            with st.expander(f"View Duty Chart: {teacher}"):
                st.table(df_t)
                pdf_t_bytes = create_pdf("Global Excellence Academy", f"Faculty Duty Chart: {teacher}", df_t)
                st.download_button(f"📥 Download {teacher}'s PDF", pdf_t_bytes, f"Teacher_{teacher}.pdf", "application/pdf")
