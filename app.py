import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Config
st.set_page_config(page_title="GEA Timetable ERP", layout="wide")

# 2. Security (Profit Level 200)
MASTER_KEY = "AhsanPro200"
def check_license():
    if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
    if not st.session_state['authenticated']:
        st.title("🔐 System Activation")
        user_key = st.text_input("Enter License Key", type="password")
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
    except Exception: return None

if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Automated Timetable ERP - Final Master Version")

    # --- SETTINGS ---
    with st.sidebar:
        st.header("⏰ Timing Controls")
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("Start Time", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("Closing Time", datetime.strptime("14:00", "%H:%M"))
        period_duration = st.number_input("Period (Mins)", 10, 120, 45)
        st.divider()
        after_p = st.number_input("Break After Period", 1, 10, 4)
        break_len = st.number_input("Break (Mins)", 10, 60, 30)

    # --- FACULTY & CLASSES ---
    st.markdown("### 🏛️ Section-Wise Teacher & Subject Assignment")
    t1, t2, t3 = st.tabs(["Primary Section", "Secondary Section", "College Section"])

    def manage_section(label):
        col_c, col_f = st.columns([1, 2])
        classes = col_c.text_area(f"{label} Classes", "Grade 1, Grade 2")
        
        # Teacher-Subject Table
        st.write(f"Add {label} Teachers and their specific Subjects:")
        df_input = pd.DataFrame([{"Teacher Name": "", "Subject": ""}] * 5)
        edited_df = col_f.data_editor(df_input, num_rows="dynamic", key=f"editor_{label}")
        
        # Clean data
        valid_teachers = edited_df[edited_df["Teacher Name"] != ""]
        teacher_list = [f"{row['Teacher Name']} ({row['Subject']})" for _, row in valid_teachers.iterrows()]
        return [c.strip() for c in classes.split(",")], teacher_list

    with t1: pri_c, pri_t = manage_section("Primary")
    with t2: sec_c, sec_t = manage_section("Secondary")
    with t3: coll_c, coll_t = manage_section("College")

    # --- GENERATION ENGINE ---
    if st.button("🚀 Generate All Professional Timetables"):
        sections = [
            {"name": "Primary", "classes": pri_c, "teachers": pri_t},
            {"name": "Secondary", "classes": sec_c, "teachers": sec_t},
            {"name": "College", "classes": coll_c, "teachers": coll_t}
        ]
        
        master_registry = {}
        all_faculty = pri_t + sec_t + coll_t

        # Smart Time Logic
        time_slots = []
        curr = datetime.combine(datetime.today(), school_start)
        closing = datetime.combine(datetime.today(), school_end)
        p_num = 1
        while curr + timedelta(minutes=period_duration) <= closing:
            ts = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=period_duration)).strftime('%I:%M %p')}"
            time_slots.append({"label": f"P{p_num}", "time": ts, "is_break": False})
            curr += timedelta(minutes=period_duration)
            if p_num == after_p and curr + timedelta(minutes=break_len) <= closing:
                ts_b = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=break_len)).strftime('%I:%M %p')}"
                time_slots.append({"label": "BREAK", "time": ts_b, "is_break": True})
                curr += timedelta(minutes=break_len)
            p_num += 1

        # Class Schedules
        st.header("📋 Student Class Schedules")
        for sec in sections:
            for cls in sec["classes"]:
                cls_sched = {}
                for day in days:
                    day_plan = []
                    for slot in time_slots:
                        if slot["is_break"]: day_plan.append("BREAK")
                        else:
                            avail = [t for t in sec["teachers"] if (day, slot["time"], t) not in master_registry]
                            if avail:
                                t_info = random.choice(avail)
                                master_registry[(day, slot["time"], t_info)] = cls
                                day_plan.append(t_info)
                            else: day_plan.append("-")
                    cls_sched[day] = day_plan
                
                df_cls = pd.DataFrame(cls_sched, index=[s['time'] for s in time_slots])
                st.write(f"**Class: {cls}**")
                st.table(df_cls)
                pdf_c = create_pdf("Global Excellence Academy", f"Class Schedule: {cls}", df_cls)
                st.download_button(f"📥 Download {cls} PDF", pdf_c, f"{cls}.pdf")

        # Teacher Schedules
        st.divider()
        st.header("👨‍🏫 Teacher Duty Charts")
        for t in all_faculty:
            t_sched = {}
            for day in days:
                t_plan = []
                for slot in time_slots:
                    if slot["is_break"]: t_plan.append("RECESSS")
                    else: t_plan.append(master_registry.get((day, slot["time"], t), "FREE"))
                t_sched[day] = t_plan
            df_t = pd.DataFrame(t_sched, index=[s['time'] for s in time_slots])
            with st.expander(f"Duty Chart: {t}"):
                st.table(df_t)
                pdf_t = create_pdf("Global Excellence Academy", f"Teacher Duty Chart: {t}", df_t)
                st.download_button(f"📥 Download PDF ({t})", pdf_t, f"Teacher_{t}.pdf")
