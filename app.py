import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# 1. Page Configuration & Professional Branding
st.set_page_config(page_title="Global Excellence Academy ERP", layout="wide")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# 2. Security & License Management (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31"

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if not st.session_state['authenticated']:
        st.title("🔐 Software Activation Required")
        st.info("Global Excellence Academy - Professional Timetable System")
        user_key = st.text_input("Enter License Master Key", type="password")
        if st.button("Activate License"):
            if user_key == MASTER_KEY:
                current_date = datetime.now().date()
                expiry = datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date()
                if current_date <= expiry:
                    st.session_state['authenticated'] = True
                    st.success("System Activated Successfully!")
                    st.rerun()
                else:
                    st.error("License Expired. Contact Administrator.")
            else:
                st.error("Invalid Key. Access Denied.")
        return False
    return True

# 3. Robust PDF Generation Function (Prevents Encoding Errors)
def create_pdf(header_title, sub_title, df):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        # Header
        pdf.cell(190, 10, str(header_title), ln=True, align='C')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, str(sub_title), ln=True, align='C')
        pdf.ln(10)
        
        # Table Setup
        pdf.set_font("Arial", 'B', 8)
        cols = ["Time Slot"] + list(df.columns)
        w = 190 / len(cols)
        for col in cols:
            pdf.cell(w, 10, str(col), 1, 0, 'C')
        pdf.ln()
        
        # Table Content
        pdf.set_font("Arial", '', 7)
        for i in range(len(df)):
            pdf.cell(w, 10, str(df.index[i]), 1, 0, 'C')
            for col in df.columns:
                # Cleaning text to ensure PDF compatibility
                clean_text = str(df[col][i]).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(w, 10, clean_text, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

# 4. Main Application Logic
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Enterprise Resource Planning (ERP) - Timetable Module")

    # --- Sidebar Settings ---
    with st.sidebar:
        st.header("⚙️ School Configuration")
        days = st.multiselect("Select Working Days", 
                             ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], 
                             ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        st.divider()
        st.subheader("⏰ School Timing")
        school_start = st.time_input("School Start Time", datetime.strptime("08:00", "%H:%M"))
        period_duration = st.number_input("Period Duration (Mins)", 10, 120, 45)
        
        st.divider()
        st.subheader("☕ Break / Recess")
        after_period = st.number_input("Break After Period No.", 1, 10, 4)
        break_duration = st.number_input("Break Duration (Mins)", 10, 60, 30)

    # --- Section Management ---
    st.markdown("### 🏛️ Faculty & Section Data")
    tab1, tab2, tab3 = st.tabs(["👶 Primary Section", "🏫 Secondary Section", "🎓 College Section"])
    
    with tab1:
        c1, c2 = st.columns(2)
        pri_classes = c1.text_area("Primary Classes", "Grade 1, Grade 2, Grade 3")
        pri_teachers = c2.text_area("Primary Teachers", "Ms. Fatima, Ms. Zainab, Mr. Ali")
    
    with tab2:
        c1, c2 = st.columns(2)
        sec_classes = c1.text_area("Secondary Classes", "Grade 6, Grade 7, Grade 8")
        sec_teachers = c2.text_area("Secondary Teachers", "Mr. Sajid, Ms. Hina, Mr. Junaid")
    
    with tab3:
        c1, c2 = st.columns(2)
        coll_classes = c1.text_area("College Classes", "FSc Medical, FSc Engineering, A-Levels")
        coll_teachers = c2.text_area("College Teachers", "Dr. Smith, Prof. Ahmed, Dr. Zehra")

    subjects_input = st.text_input("Academic Subjects (Comma separated)", "Mathematics, Physics, Chemistry, English, Urdu, Science")

    # --- Generation Engine ---
    if st.button("🚀 Generate Master Schedules & PDF Reports"):
        sections = [
            {"name": "Primary", "classes": [c.strip() for c in pri_classes.split(",")], "teachers": [t.strip() for t in pri_teachers.split(",")]},
            {"name": "Secondary", "classes": [c.strip() for c in sec_classes.split(",")], "teachers": [t.strip() for t in sec_teachers.split(",")]},
            {"name": "College", "classes": [c.strip() for c in coll_classes.split(",")], "teachers": [t.strip() for t in coll_teachers.split(",")]}
        ]
        subjects_list = [s.strip() for s in subjects_input.split(",")]
        
        master_registry = {} # Stores teacher assignments to prevent clashes
        all_faculty = []
        for s in sections: all_faculty.extend(s["teachers"])

        # Calculate Time Slots
        time_slots = []
        curr_time = datetime.combine(datetime.today(), school_start)
        for i in range(1, 10): # Max 9 periods
            start_s = curr_time.strftime('%I:%M %p')
            end_t_obj = curr_time + timedelta(minutes=period_duration)
            end_s = end_t_obj.strftime('%I:%M %p')
            time_slots.append({"label": f"Period {i}", "time": f"{start_s}-{end_s}", "is_break": False})
            curr_time = end_t_obj
            if i == after_period:
                b_end = curr_time + timedelta(minutes=break_duration)
                time_slots.append({"label": "BREAK", "time": f"{curr_time.strftime('%I:%M %p')}-{b_end.strftime('%I:%M %p')}", "is_break": True})
                curr_time = b_end

        # 1. Output Class Timetables
        st.header("📋 Student Class Timetables")
        for sec in sections:
            for cls in sec["classes"]:
                cls_schedule = {}
                for day in days:
                    day_plan = []
                    for slot in time_slots:
                        if slot["is_break"]: day_plan.append("☕ BREAK")
                        else:
                            available = [t for t in sec["teachers"] if (day, slot["time"], t) not in master_registry]
                            if available:
                                teacher = random.choice(available)
                                subject = random.choice(subjects_list)
                                master_registry[(day, slot["time"], teacher)] = f"{cls} ({subject})"
                                day_plan.append(f"{teacher}\n({subject})")
                            else: day_plan.append("❌ NO STAFF")
                    cls_schedule[day] = day_plan
                
                df_cls = pd.DataFrame(cls_schedule, index=[s['time'] for s in time_slots])
                st.write(f"**Timetable: {cls}**")
                st.table(df_cls)
                pdf_c = create_pdf("Global Excellence Academy", f"Class Schedule: {cls}", df_cls)
                if pdf_c: st.download_button(f"📥 Download {cls} PDF", pdf_c, f"{cls}_Schedule.pdf", "application/pdf")

        # 2. Output Teacher Duty Charts
        st.divider()
        st.header("👨‍🏫 Faculty Personal Duty Charts")
        for teacher in all_faculty:
            t_schedule = {}
            for day in days:
                t_plan = []
                for slot in time_slots:
                    if slot["is_break"]: t_plan.append("RECESSS")
                    else:
                        duty = master_registry.get((day, slot["time"], teacher), "FREE PERIOD")
                        t_plan.append(duty)
                t_schedule[day] = t_plan
            
            df_t = pd.DataFrame(t_schedule, index=[s['time'] for s in time_slots])
            with st.expander(f"View Schedule: {teacher}"):
                st.table(df_t)
                pdf_t = create_pdf("Global Excellence Academy", f"Teacher Duty Chart: {teacher}", df_t)
                if pdf_t: st.download_button(f"📥 Download {teacher} PDF", pdf_t, f"Teacher_{teacher}.pdf", "application/pdf")
