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

# 3. PDF Generator Function
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
    st.subheader("Professional ERP: Class Timetables & Teacher Duty Charts")

    # Sidebar: Timing Settings
    with st.sidebar:
        st.header("⏰ Timing Controls")
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("School Start", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("School End", datetime.strptime("14:00", "%H:%M"))
        period_duration = st.number_input("Period Duration (Mins)", 10, 120, 40)
        st.divider()
        after_p = st.number_input("Break After Period", 1, 10, 4)
        break_len = st.number_input("Break Mins", 10, 60, 30)

    # Input Section: Dynamic Tables
    st.markdown("### 🏛️ Data Entry: Teachers & Classes")
    tab1, tab2, tab3 = st.tabs(["Primary Section", "Secondary Section", "College Section"])

    def get_section_input(key, def_classes):
        c_col, t_col = st.columns([1, 2])
        cls_raw = c_col.text_area("Classes (Comma Separated)", def_classes, key=f"cls_{key}")
        cls_list = [c.strip() for c in cls_raw.split(",") if c.strip()]
        st.write("Assign Teachers and Subjects:")
        df_init = pd.DataFrame([{"Name": "", "Subject": ""}] * 5)
        edited = t_col.data_editor(df_init, num_rows="dynamic", key=f"table_{key}")
        teachers = [f"{r['Name']} ({r['Subject']})" for _, r in edited.iterrows() if r["Name"]]
        return cls_list, teachers

    with tab1: pri_c, pri_t = get_section_input("pri", "Grade 1, Grade 2")
    with tab2: sec_c, sec_t = get_section_input("sec", "Grade 9, Grade 10")
    with tab3: coll_c, coll_t = get_section_input("coll", "FSc, BS")

    if st.button("🚀 Generate All Timetables"):
        # 1. Generate Time Slots
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

        if not time_slots:
            st.error("Time range is too short.")
        else:
            master_schedule = {} # (day, time, teacher) -> class
            sections = [
                {"name": "Primary", "classes": pri_c, "teachers": pri_t},
                {"name": "Secondary", "classes": sec_c, "teachers": sec_t},
                {"name": "College", "classes": coll_c, "teachers": coll_t}
            ]

            # --- PART 1: GENERATE ALL CLASS TIMETABLES ---
            st.markdown("---")
            st.header("📋 SECTION 1: STUDENT CLASS TIMETABLES")
            for sec in sections:
                if not sec["classes"]: continue
                st.subheader(f"📍 {sec['name']} Section")
                for cls in sec["classes"]:
                    cls_df_dict = {}
                    for day in days:
                        day_plan = []
                        for slot in time_slots:
                            if slot["is_break"]: day_plan.append("BREAK")
                            else:
                                avail = [t for t in sec["teachers"] if (day, slot["time"], t) not in master_schedule]
                                if avail:
                                    t_choice = random.choice(avail)
                                    master_schedule[(day, slot["time"], t_choice)] = cls
                                    day_plan.append(t_choice)
                                else: day_plan.append("FREE / NO STAFF")
                        cls_df_dict[day] = day_plan
                    
                    df_cls = pd.DataFrame(cls_df_dict, index=[s['time'] for s in time_slots])
                    st.write(f"**Timetable for Class: {cls}**")
                    st.table(df_cls)
                    pdf_c = create_pdf("Global Excellence Academy", f"Class Schedule: {cls}", df_cls)
                    st.download_button(f"📥 Download PDF for {cls}", pdf_c, f"{cls}.pdf", key=f"cls_btn_{cls}")

            # --- PART 2: GENERATE ALL TEACHER DUTY CHARTS ---
            st.markdown("---")
            st.header("👨‍🏫 SECTION 2: FACULTY DUTY CHARTS")
            all_teachers = pri_t + sec_t + coll_t
            for teacher in all_teachers:
                t_df_dict = {}
                for day in days:
                    t_day_plan = []
                    for slot in time_slots:
                        if slot["is_break"]: t_day_plan.append("BREAK / LUNCH")
                        else:
                            assigned_class = master_schedule.get((day, slot["time"], teacher), "FREE PERIOD")
                            t_day_plan.append(assigned_class)
                    t_df_dict[day] = t_day_plan
                
                df_t = pd.DataFrame(t_df_dict, index=[s['time'] for s in time_slots])
                with st.expander(f"View Duty Chart for {teacher}"):
                    st.table(df_t)
                    pdf_t = create_pdf("Global Excellence Academy", f"Teacher Duty Chart: {teacher}", df_t)
                    st.download_button(f"📥 Download PDF for {teacher}", pdf_t, f"Teacher_{teacher}.pdf", key=f"t_btn_{teacher}")
