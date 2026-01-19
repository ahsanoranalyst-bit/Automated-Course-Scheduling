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
    st.subheader("Complete ERP: Primary, Secondary & College Timetables")

    # --- SIDEBAR SETTINGS ---
    with st.sidebar:
        st.header("⏰ Timing Controls")
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("Start Time", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("Closing Time", datetime.strptime("14:00", "%H:%M"))
        period_duration = st.number_input("Period Duration (Mins)", 10, 120, 40)
        st.divider()
        after_p = st.number_input("Break After Period", 1, 10, 4)
        break_len = st.number_input("Break Length (Mins)", 10, 60, 30)

    # --- INPUT SECTION ---
    st.markdown("### 🏛️ Manage Teachers & Classes")
    tab1, tab2, tab3 = st.tabs(["Primary Section", "Secondary Section", "College Section"])

    def get_section_data(key_prefix, default_classes):
        col_c, col_f = st.columns([1, 2])
        classes_raw = col_c.text_area(f"Classes List", default_classes, key=f"cls_{key_prefix}")
        classes_list = [c.strip() for c in classes_raw.split(",") if c.strip()]
        
        st.write(f"Add Teachers & Subjects:")
        # Start with a clean 5-row table
        init_data = [{"Teacher Name": "", "Subject": ""}] * 5
        edited_df = col_f.data_editor(pd.DataFrame(init_data), num_rows="dynamic", key=f"ed_{key_prefix}")
        
        # Format: "Teacher Name (Subject)"
        teachers_list = []
        for _, row in edited_df.iterrows():
            if row["Teacher Name"]:
                teachers_list.append(f"{row['Teacher Name']} ({row['Subject']})")
        return classes_list, teachers_list

    with tab1: pri_c, pri_t = get_section_data("pri", "Grade 1, Grade 2, Grade 3")
    with tab2: sec_c, sec_t = get_section_data("sec", "Grade 9, Grade 10")
    with tab3: coll_c, coll_t = get_section_data("coll", "FSc-1, FSc-2")

    if st.button("🚀 Generate All Timetables"):
        sections = [
            {"name": "Primary", "classes": pri_c, "teachers": pri_t},
            {"name": "Secondary", "classes": sec_c, "teachers": sec_t},
            {"name": "College", "classes": coll_c, "teachers": coll_t}
        ]
        
        # 1. Calculate Time Slots
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
            st.error("Timing Error: Opening and Closing times are too close.")
        else:
            master_schedule = {} # (day, time, teacher) -> class
            all_class_tables = {} # class -> dataframe

            # 2. Process Each Section
            for sec in sections:
                if not sec["classes"]: continue
                st.header(f"🏁 {sec['name']} Section")
                
                for cls in sec["classes"]:
                    cls_data = {}
                    for day in days:
                        day_plan = []
                        for slot in time_slots:
                            if slot["is_break"]: day_plan.append("☕ BREAK")
                            else:
                                # Logic: Find a teacher from THIS section who is FREE at THIS time
                                avail = [t for t in sec["teachers"] if (day, slot["time"], t) not in master_schedule]
                                if avail:
                                    t_choice = random.choice(avail)
                                    master_schedule[(day, slot["time"], t_choice)] = cls
                                    day_plan.append(t_choice)
                                else:
                                    day_plan.append("❌ NO STAFF")
                        cls_data[day] = day_plan
                    
                    df_cls = pd.DataFrame(cls_data, index=[s['time'] for s in time_slots])
                    st.write(f"**Timetable for {cls}**")
                    st.table(df_cls)
                    
                    pdf_c = create_pdf("Global Excellence Academy", f"Class: {cls}", df_cls)
                    st.download_button(f"📥 Download PDF ({cls})", pdf_c, f"{cls}.pdf", key=f"btn_{cls}")

            # 3. Process Teacher Schedules
            st.divider()
            st.header("👨‍🏫 Teacher Personal Duty Charts")
            all_t = pri_t + sec_t + coll_t
            for t in all_t:
                t_data = {}
                for day in days:
                    t_day = []
                    for slot in time_slots:
                        if slot["is_break"]: t_day.append("BREAK")
                        else:
                            assigned_to = master_schedule.get((day, slot["time"], t), "FREE")
                            t_day.append(assigned_to)
                    t_data[day] = t_day
                
                df_t = pd.DataFrame(t_data, index=[s['time'] for s in time_slots])
                with st.expander(f"Duty Chart: {t}"):
                    st.table(df_t)
                    pdf_t = create_pdf("Global Excellence Academy", f"Teacher Duty: {t}", df_t)
                    st.download_button(f"📥 Download PDF ({t})", pdf_t, f"Teacher_{t}.pdf", key=f"tbtn_{t}")
