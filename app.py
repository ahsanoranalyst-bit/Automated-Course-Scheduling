


import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Configuration
st.set_page_config(page_title="Automated Course Scheduling Optimizer", layout="wide")

# 2. Security (Profit Level 200)
MASTER_KEY = "Ahsan123"
EXPIRY_DATE = "2030-12-31"

def check_license():
    if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error(" LICENSE EXPIRED!")
        return False
    if not st.session_state['authenticated']:
        st.title(" Automated Course Scheduling Optimizer Activation")
        user_key = st.text_input("Enter Activation Key:", type="password")
        if st.button("Activate"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Invalid Key")
        return False
    return True

# 3. PDF Generator
def create_pdf(school_name, header, sub, df):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(190, 15, str(school_name).upper(), ln=True, align='C')
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, str(header), ln=True, align='C')
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(190, 8, str(sub), ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 9)
        cols = ["Time Slot"] + list(df.columns)
        w = 190 / len(cols)
        for col in cols: pdf.cell(w, 10, str(col), 1, 0, 'C')
        pdf.ln()
        pdf.set_font("Arial", '', 8)
        for i in range(len(df)):
            pdf.cell(w, 10, str(df.index[i]), 1, 0, 'C')
            for col in df.columns:
                val = str(df[col][i]).encode('ascii', 'ignore').decode('ascii')
                pdf.cell(w, 10, val, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# 4. Main ERP Logic
if check_license():
    with st.sidebar:
        st.header(" School Setup")
        custom_school_name = st.text_input("Enter School Name:", "Global Excellence Academy")
        st.divider()
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_t = st.time_input("Open", datetime.strptime("08:00", "%H:%M"))
        end_t = st.time_input("Close", datetime.strptime("14:00", "%H:%M"))
        p_mins = st.number_input("Period Duration", 10, 120, 40)
        brk_after = st.number_input("Break After Period", 1, 10, 4)
        brk_mins = st.number_input("Break Mins", 10, 60, 30)
       
        # --- SIDEBAR BUTTONS ---
        st.divider()
        if st.button("Save Configuration", use_container_width=True, type="primary"):
            st.sidebar.success("Settings Saved!")
           
        if st.button("Logout", use_container_width=True):
            st.session_state['authenticated'] = False
            st.rerun()

    st.title(f" {custom_school_name}")
   
    # Registration Tabs
    tab1, tab2, tab3 = st.tabs(["Primary Registration", "Secondary Registration", "College Registration"])
   
    with tab1:
        col1, col2 = st.columns([1, 2])
        p_c_df = col1.data_editor(pd.DataFrame([{"Class": "Grade 1", "Sections": 1}]), num_rows="dynamic", key="p_c")
        p_t_df = col2.data_editor(pd.DataFrame([{"Name": "", "Subject": ""}] * 5), num_rows="dynamic", key="p_t")
    with tab2:
        col1, col2 = st.columns([1, 2])
        s_c_df = col1.data_editor(pd.DataFrame([{"Class": "Grade 9", "Sections": 1}]), num_rows="dynamic", key="s_c")
        s_t_df = col2.data_editor(pd.DataFrame([{"Name": "", "Subject": ""}] * 5), num_rows="dynamic", key="s_t")
    with tab3:
        col1, col2 = st.columns([1, 2])
        c_c_df = col1.data_editor(pd.DataFrame([{"Class": "FSc-1", "Sections": 1}]), num_rows="dynamic", key="c_c")
        c_t_df = col2.data_editor(pd.DataFrame([{"Name": "", "Subject": ""}] * 5), num_rows="dynamic", key="c_t")

    if st.button(" Run Analysis"):
        # Processing Data
        def process_list(c_df, t_df):
            cls = []
            for _, r in c_df.iterrows():
                if r["Class"]:
                    for i in range(int(r["Sections"])): cls.append(f"{r['Class']} (Sec {i+1})")
            tea = [f"{r['Name']} ({r['Subject']})" for _, r in t_df.iterrows() if r["Name"]]
            return cls, tea

        p_cls, p_tea = process_list(p_c_df, p_t_df)
        s_cls, s_tea = process_list(s_c_df, s_t_df)
        c_cls, c_tea = process_list(c_c_df, c_t_df)

        # Slots
        slots = []
        curr = datetime.combine(datetime.today(), start_t)
        limit = datetime.combine(datetime.today(), end_t)
        idx = 1
        while curr + timedelta(minutes=p_mins) <= limit:
            t_str = f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=p_mins)).strftime('%I:%M %p')}"
            slots.append({"time": t_str, "brk": False})
            curr += timedelta(minutes=p_mins)
            if idx == brk_after and curr + timedelta(minutes=brk_mins) <= limit:
                slots.append({"time": f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=brk_mins)).strftime('%I:%M %p')}", "brk": True})
                curr += timedelta(minutes=brk_mins)
            idx += 1

        # Scheduling Logic
        master = {}; class_schedules = {}; stats = {"Primary": {"T":0, "F":0}, "Secondary": {"T":0, "F":0}, "College": {"T":0, "F":0}}
        all_sections = [{"id": "Primary", "c": p_cls, "t": p_tea}, {"id": "Secondary", "c": s_cls, "t": s_tea}, {"id": "College", "c": c_cls, "t": c_tea}]

        for sec in all_sections:
            for cls in sec["c"]:
                day_plans = {}
                for d in days:
                    slot_list = []
                    for s in slots:
                        if s["brk"]: slot_list.append(" BREAK")
                        else:
                            stats[sec["id"]]["T"] += 1
                            avail = [t for t in sec["t"] if (d, s["time"], t) not in master and (d, cls, t) not in master]
                            if avail:
                                pk = random.choice(avail); master[(d, s["time"], pk)] = cls
                                master[(d, cls, pk)] = True; slot_list.append(pk); stats[sec["id"]]["F"] += 1
                            else: slot_list.append(" NO STAFF")
                    day_plans[d] = slot_list
                class_schedules[cls] = pd.DataFrame(day_plans, index=[s['time'] for s in slots])

        # --- DISPLAY 1: ANALYTICS (TOP) ---
        st.markdown("---")
        st.header(f" {custom_school_name}: Profit & Efficiency Analysis")
       
        # Total Stats
        m1, m2, m3 = st.columns(3)
        all_f = sum(x["F"] for x in stats.values()); all_t = sum(x["T"] for x in stats.values())
        eff = (all_f / all_t * 100) if all_t > 0 else 0
        m1.metric("Overall Efficiency", f"{eff:.1f}%")
        m2.metric("Total Active Sections", len(class_schedules))
        m3.metric("Profit Status", "Optimized" if eff > 85 else "Action Required")

        # --- FIXED SECTION PERFORMANCE IN ONE LINE ---
        st.write("####  Section-Wise Performance (Primary | Secondary | College)")
        s_col1, s_col2, s_col3 = st.columns(3)

        with s_col1:
            p_e = (stats["Primary"]["F"]/stats["Primary"]["T"]*100) if stats["Primary"]["T"] > 0 else 0
            st.info(f"**PRIMARY**\n\nEfficiency: {p_e:.1f}%\nVacancies: {stats['Primary']['T']-stats['Primary']['F']}")
       
        with s_col2:
            s_e = (stats["Secondary"]["F"]/stats["Secondary"]["T"]*100) if stats["Secondary"]["T"] > 0 else 0
            st.info(f"**SECONDARY**\n\nEfficiency: {s_e:.1f}%\nVacancies: {stats['Secondary']['T']-stats['Secondary']['F']}")
           
        with s_col3:
            c_e = (stats["College"]["F"]/stats["College"]["T"]*100) if stats["College"]["T"] > 0 else 0
            st.info(f"**COLLEGE**\n\nEfficiency: {c_e:.1f}%\nVacancies: {stats['College']['T']-stats['College']['F']}")

        # --- DISPLAY 2: CLASS SCHEDULES ---
        st.markdown("---")
        st.header(" Student Class Schedules")
        for cls_name, df in class_schedules.items():
            with st.expander(f"View: {cls_name}"):
                st.table(df)
                p = create_pdf(custom_school_name, "STUDENT TIMETABLE", f"Class: {cls_name}", df)
                st.download_button(f" Print {cls_name} PDF", p, f"{cls_name}.pdf", "application/pdf", key=f"b_{cls_name}")

        # --- DISPLAY 3: TEACHER DUTIES ---
        st.markdown("---")
        st.header(" Teacher Duty Charts")
        for t in (p_tea + s_tea + c_tea):
            t_duty = {d: [master.get((d, s["time"], t), "FREE") if not s["brk"] else "BREAK" for s in slots] for d in days}
            df_t = pd.DataFrame(t_duty, index=[s['time'] for s in slots])
            with st.expander(f"View: {t}"):
                st.table(df_t)
                tp = create_pdf(custom_school_name, "TEACHER DUTY CHART", f"Teacher: {t}", df_t)
                st.download_button(f" Print {t} PDF", tp, f"{t}.pdf", "application/pdf", key=f"tb_{t}")

