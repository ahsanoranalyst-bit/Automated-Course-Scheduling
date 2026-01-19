import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Config
st.set_page_config(page_title="GEA Timetable ERP", layout="wide")

# 2. Advanced Security & Software Lock (Profit Level 200)
MASTER_KEY = "AhsanPro200"
# Admin can update this date to extend license
EXPIRY_DATE = "2026-12-31" 

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    # Logic: If Current Date > Expiry Date, Lock the System
    current_date = datetime.now().date()
    expiry = datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date()
    
    if current_date > expiry:
        st.error("❌ LICENSE EXPIRED! Please contact the administrator (Ahsan) for a system update.")
        st.info(f"System Lock Date: {EXPIRY_DATE}")
        return False

    if not st.session_state['authenticated']:
        st.title("🔐 Software Activation")
        st.warning("Global Excellence Academy - Enterprise Edition")
        user_key = st.text_input("Enter Master License Key to Unlock:", type="password")
        if st.button("Activate System"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.success("Access Granted! Loading ERP...")
                st.rerun()
            else:
                st.error("Invalid License Key. Access Denied.")
        return False
    return True

# 3. PDF Function
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
                text = str(df[col][i]).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(w, 10, text, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# 4. Main ERP Application
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Smart ERP: No-Repeat Logic & Professional Security")

    with st.sidebar:
        st.header("⏰ School Timings")
        days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("School Start Time", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("Closing Time", datetime.strptime("14:00", "%H:%M"))
        period_duration = st.number_input("Period Duration (Mins)", 10, 120, 40)
        st.divider()
        after_p = st.number_input("Break After Period", 1, 10, 4)
        break_len = st.number_input("Break Mins", 10, 60, 30)

    # Section Tabs
    st.markdown("### 🏛️ Data Entry")
    tab1, tab2, tab3 = st.tabs(["Primary Section", "Secondary Section", "College Section"])

    def get_section_input(key, def_classes):
        c_col, t_col = st.columns([1, 2])
        cls_raw = c_col.text_area("Classes (e.g. Grade 1, Grade 2)", def_classes, key=f"cls_{key}")
        cls_list = [c.strip() for c in cls_raw.split(",") if c.strip()]
        st.write("Enter Teachers & Subjects:")
        df_init = pd.DataFrame([{"Name": "", "Subject": ""}] * 5)
        edited = t_col.data_editor(df_init, num_rows="dynamic", key=f"table_{key}")
        teachers = [f"{r['Name']} ({r['Subject']})" for _, r in edited.iterrows() if r["Name"]]
        return cls_list, teachers

    with tab1: pri_c, pri_t = get_section_input("pri", "Grade 1, Grade 2")
    with tab2: sec_c, sec_t = get_section_input("sec", "Grade 9, Grade 10")
    with tab3: coll_c, coll_t = get_section_input("coll", "FSc, BS")

    if st.button("🚀 Generate Optimized Timetables"):
        # Time Slots Logic
        time_slots = []
        curr = datetime.combine(datetime.today(), school_start)
        closing = datetime.combine(datetime.today(), school_end)
        p_num = 1
        while curr + timedelta(minutes=period_duration) <= closing:
            ts = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=period_duration)).strftime('%I:%M %p')}"
            time_slots.append({"label": f"P{p_num}", "time
