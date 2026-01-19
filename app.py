import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Config
st.set_page_config(page_title="GEA Timetable ERP", layout="wide")

# 2. Security (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31" 

def check_license():
    if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error("❌ LICENSE EXPIRED!")
        return False
    if not st.session_state['authenticated']:
        st.title("🔐 Enterprise System Activation")
        user_key = st.text_input("Enter License Key:", type="password")
        if st.button("Activate"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Invalid Key")
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
        pdf.set_font("Arial", 'B', 8); cols = ["Time Slot"] + list(df.columns)
        w = 190 / len(cols)
        for col in cols: pdf.cell(w, 10, str(col), 1, 0, 'C')
        pdf.ln()
        pdf.set_font("Arial", '', 7)
        for i in range(len(df)):
            pdf.cell(w, 10, str(df.index[i]), 1, 0, 'C')
            for col in df.columns:
                val = str(df[col][i]).encode('ascii', 'ignore').decode('ascii')
                pdf.cell(w, 10, val, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S')
    except: return None

# 4. App Logic
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("ERP: Multi-Section & Room Optimization Dashboard")

    with st.sidebar:
        st.header("⚙️ Global Settings")
        work_days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_t = st.time_input("Opening", datetime.strptime("08:00", "%H:%M"))
        end_t = st.time_input("Closing", datetime.strptime("14:00", "%H:%M"))
        p_dur = st.number_input("Period Mins", 10, 120, 40)
        st.divider()
        break_after = st.number_input("Break After Period", 1, 10, 4)
        break_mins = st.number_input("Break Length", 10, 60, 30)

    # --- Section Management with Room Input ---
    st.header("🏛️ Section & Room Allocation")
    t1, t2, t3 = st.tabs(["Primary", "Secondary", "College"])
    
    def get_detailed_data(key, def_val):
        st.write(f"### {key} Section Setup")
        c1, c2 = st.columns([1, 2])
        # Multi-Section Input
        raw_input = c1.data_editor(pd.DataFrame([{"Class": "Grade 1", "Rooms/Sections": 1}, {"Class": "Grade 2", "Rooms/Sections": 1}]), num_rows="dynamic", key=f"cls_room_{key}")
        
        # Teacher Input
        st.write("Assign Teachers:")
        tea_df = c2.data_editor(pd.DataFrame([{"Teacher": "", "Subject": ""}] * 5), num_rows="dynamic", key=f"t_ed_{key}")
        teachers = [f"{r['Teacher']} ({r['Subject']})" for _, r in tea_df.iterrows() if r["Teacher"]]
        
        # Flatten classes based on rooms
        final_classes = []
        for _, row in raw_input.iterrows():
            for i in range(int(row["Rooms/Sections"])):
                final_classes.append(f"{row['Class']} (Room {i+1})")
        return final_classes, teachers

    with t1: p_cls, p_tea = get_detailed_data("Primary", "Grade 1")
    with t2: s_cls, s_tea = get_detailed_data("Secondary", "Grade 9")
    with t3: col_cls, col_tea = get_detailed_data("College", "FSc")

    if st.button("🚀 Run Comprehensive Analysis"):
        # Time Slots
        slots = []
        curr = datetime.combine(datetime.today(), start_t)
        limit = datetime.combine(datetime.today(), end_t)
        idx = 1
        while curr + timedelta(minutes=p_dur) <= limit:
            tr = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=p_dur)).strftime('%I:%M %p')}"
            slots.append({"t": tr, "b": False})
            curr += timedelta(minutes=p_dur)
            if idx == break_after and curr + timedelta(minutes=break_mins) <= limit:
                slots.append({"t": f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=break_mins)).strftime('%I:%M %p')}", "b": True})
                curr += timedelta(minutes=break_mins)
            idx += 1

        if slots:
            master = {}; class_results = {}; stats = {}
            sections = [{"id": "Primary", "c": p_cls, "t": p_tea}, {"id": "Secondary", "c": s_cls, "t": s_tea}, {"id": "College", "c": col_cls, "t": col_tea}]
