import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Config
st.set_page_config(page_title="GEA Timetable ERP", layout="wide")

# 2. Security
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

if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("ERP: Class & Teacher Schedules (with No-Repeat Logic)")

    with st.sidebar:
        st.header("⏰ Timing Controls")
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("School Start", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("School End", datetime.strptime("14:00", "%H:%M"))
        period_duration = st.number_input("Period Duration (Mins)", 10, 120, 40)
        st.divider()
        after_p = st.number_input("Break After Period", 1, 10, 4)
        break_len = st.number_input("Break Mins", 10, 60, 30)

    # Input Section
    st.markdown("### 🏛️ Data Entry")
    tab1, tab2, tab3 = st.tabs(["Primary Section", "Secondary Section", "College Section"])

    def get_section_input(key, def_classes):
        c_col, t_col = st.columns([1, 2])
        cls_raw = c_col.text_area("Classes", def_classes, key=f"cls_{key}")
        cls_list = [c.strip() for c in cls_raw.split(",") if c.strip()]
        df_init = pd.DataFrame([{"Name": "", "Subject": ""}] * 5)
        edited = t_col.data_editor(df_init, num_rows="dynamic", key=f"table_{key}")
        teachers = [f"{r['Name']} ({r['Subject']})" for _, r in edited.iterrows() if r["Name"]]
        return cls_list, teachers

    with tab1: pri_c, pri_t = get_section_input("pri", "Grade 1, Grade 2")
    with tab2: sec_c, sec_t = get_section_input("sec", "Grade 9, Grade 10")
    with tab3: coll_c, coll_t = get_section_input("coll", "FSc, BS")

    if st.button("🚀 Generate All Timetables"):
        # 1. Time Slots
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
            st.error("Timing Error.")
        else:
            master_schedule = {} # (day, time, teacher) -> class
            daily_class_teachers = {} # (day, class) -> list of teachers who already taught
            
            sections = [
                {"name": "Primary", "classes": pri_c, "teachers": pri_t},
                {"name": "Secondary", "classes": sec_c, "teachers": sec_t},
                {"name": "College", "classes": coll_c, "teachers": coll_t}
            ]

            # --- PART 1: CLASSES ---
            st.header("📋 SECTION 1: STUDENT CLASS TIMETABLES")
            for sec in sections:
                if not sec["classes"]: continue
                for cls in sec["classes"]:
                    cls_dict = {}
                    for day in days:
                        day_plan = []
                        for slot in time_slots:
                            if slot["is_break"]:
                                day_plan.append("BREAK")
                            else:
                                # Logic: Teacher must be free AND must NOT have taught this class today
                                if (day, cls) not in daily_class_teachers:
                                    daily_class_teachers[(day, cls)] = []
                                
                                avail = [t for t in sec["teachers"] if 
                                         (day, slot["time"], t) not in master_schedule and 
                                         t not in daily_class_teachers[(day, cls)]]
                                
                                if avail:
                                    t_choice = random.choice(avail)
                                    master_schedule[(day, slot["time"], t_choice)] = cls
                                    daily_class_teachers[(day, cls)].append(t_choice)
                                    day_plan.append(t_choice)
                                else:
                                    day_plan.append("❌ NO STAFF")
                        cls_dict[day] = day_plan
                    
                    df_cls = pd.DataFrame(cls_dict, index=[s['time'] for s in time_slots])
                    st.write(f"**Class: {cls}**")
                    st.table(df_cls)
                    pdf_c = create_pdf("Global Excellence Academy", f"Class: {cls}", df_cls)
                    st.download_button(f"📥 Download {cls} PDF", pdf_c, f"{cls}.pdf", key=f"c_{cls}")

            # --- PART 2: TEACHERS ---
            st.divider()
            st.header("👨‍🏫 SECTION 2: FACULTY DUTY CHARTS")
            for t in (pri_t + sec_t + coll_t):
                t_dict = {}
                for day in days:
                    t_day = []
                    for slot in time_slots:
                        if slot["is_break"]: t_day.append("BREAK")
                        else:
                            t_day.append(master_schedule.get((day, slot["time"], t), "FREE"))
                    t_dict[day] = t_day
                df_t = pd.DataFrame(t_dict, index=[s['time'] for s in time_slots])
                with st.expander(f"Duty Chart: {t}"):
                    st.table(df_t)
                    pdf_t = create_pdf("Global Excellence Academy", f"Teacher: {t}", df_t)
                    st.download_button(f"📥 Download {t} PDF", pdf_t, f"Teacher_{t}.pdf", key=f"t_{t}")
