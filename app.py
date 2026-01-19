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
    expiry = datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date()
    if datetime.now().date() > expiry:
        st.error("❌ LICENSE EXPIRED!")
        return False
    if not st.session_state['authenticated']:
        st.title("🔐 Software Activation")
        user_key = st.text_input("Enter Key:", type="password")
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
        pdf.set_font("Arial", 'B', 8); cols = ["Time Slot"] + list(df.columns)
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

# 4. App Logic
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Smart ERP: Analytics & Duty Charts First")

    # --- SIDEBAR: TIMING ---
    with st.sidebar:
        st.header("⚙️ Timing Controls")
        days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("Opening Time", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("Closing Time", datetime.strptime("14:00", "%H:%M"))
        period_dur = st.number_input("Period (Mins)", 10, 120, 40)
        st.divider()
        after_p = st.number_input("Break After Period", 1, 10, 4)
        break_dur = st.number_input("Break Mins", 10, 60, 30)

    # --- DATA ENTRY ---
    st.header("🏛️ Section Management")
    t1, t2, t3 = st.tabs(["Primary", "Secondary", "College"])
    
    def get_data(key, def_c):
        c1, c2 = st.columns([1, 2])
        cl_list = [c.strip() for c in c1.text_area("Classes", def_c, key=f"c{key}").split(",") if c.strip()]
        df_in = pd.DataFrame([{"Name": "", "Subject": ""}] * 5)
        edit = c2.data_editor(df_in, num_rows="dynamic", key=f"t{key}")
        tea = [f"{r['Name']} ({r['Subject']})" for _, r in edit.iterrows() if r["Name"]]
        return cl_list, tea

    p_c, p_t = t1.get_data("pri", "Grade 1, Grade 2")
    s_c, s_t = t2.get_data("sec", "Grade 9, Grade 10")
    c_c, c_t = t3.get_data("coll", "FSc, BS")

    if st.button("🚀 Run System Analysis & Schedules"):
        # Generate Time Slots
        time_slots = []
        curr = datetime.combine(datetime.today(), school_start)
        closing = datetime.combine(datetime.today(), school_end)
        p_num = 1
        while curr + timedelta(minutes=period_dur) <= closing:
            ts = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=period_dur)).strftime('%I:%M %p')}"
            time_slots.append({"label": f"P{p_num}", "time": ts, "is_break": False})
            curr += timedelta(minutes=period_dur)
            if p_num == after_p and curr + timedelta(minutes=break_dur) <= closing:
                time_slots.append({"label": "BREAK", "time": f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=break_dur)).strftime('%I:%M %p')}", "is_break": True})
                curr += timedelta(minutes=break_dur)
            p_num += 1

        if time_slots:
            master_reg = {}; taught_today = {}; total_s = 0; filled_s = 0
            secs = [{"n": "Primary", "c": p_c, "t": p_t}, {"n": "Secondary", "c": s_c, "t": s_t}, {"n": "College", "c": c_c, "t": c_t}]
            
            # Temporary generation to calculate stats first
            for s in secs:
                for cl in s["c"]:
                    for day in days:
                        for slot in time_slots:
                            if not slot["is_break"]:
                                total_s += 1
                                if (day, cl) not in taught_today: taught_today[(day, cl)] = []
                                avail = [t for t in s["t"] if (day, slot["time"], t) not in master_reg and t not in taught_today[(day, cl)]]
                                if avail:
                                    ch = random.choice(avail)
                                    master_reg[(day, slot["time"], ch)] = cl
                                    taught_today[(day, cl)].append(ch)
                                    filled_s += 1

            # --- DISPLAY 1: PROFIT ANALYSIS (TOP) ---
            st.markdown("---")
            st.header("📊 SECTION 1: PROFIT & RESOURCE ANALYSIS")
            m1, m2, m3 = st.columns(3)
            eff = (filled_s / total_s) * 100 if total_s > 0 else 0
            m1.metric("School Efficiency Level", f"{eff:.1f}%")
            m2.metric("Unfilled Slots (Lost Profit)", total_s - filled_s)
            m3.metric("Status", "Optimized" if eff > 90 else "Understaffed", delta_color="inverse")

            # --- DISPLAY 2: TEACHER DUTY CHARTS ---
            st.markdown("---")
            st.header("👨‍🏫 SECTION 2: TEACHER DUTY CHARTS")
            all_t = p_t + s_t + c_t
            for t in all_t:
                t_plan = {day: [master_reg.get((day, slot["time"], t), "FREE") for slot in time_slots] for day in days}
                with st.expander(f"View Duty: {t}"):
                    df_t = pd.DataFrame(t_plan, index=[s['time'] for s in time_slots]); st.table(df_t)
                    pdf = create_pdf("GEA", f"Teacher: {t}", df_t)
                    st.download_button(f"Download {t} PDF", pdf, f"{t}.pdf", key=f"t_{t}")

            # --- DISPLAY 3: CLASS TIMETABLES ---
            st.markdown("---")
            st.header("📋 SECTION 3: STUDENT CLASS TIMETABLES")
            for s in secs:
                for cl in s["c"]:
                    c_plan = {day: [ (next((t for t, v in master_reg.items() if v == cl and t[0] == day and t[1] == slot["time"]), (None,None,None)))[2] or "❌ VACANT" if not slot["is_break"] else "☕ BREAK" for slot in time_slots] for day in days}
                    df_cl = pd.DataFrame(c_plan, index=[sl['time'] for sl in time_slots])
                    st.write(f"**Class: {cl}**"); st.table(df_cl)
                    pdf = create_pdf("GEA", f"Class: {cl}", df_cl)
                    st.download_button(f"Download {cl} PDF", pdf, f"{cl}.pdf", key=f"c_{cl}")
