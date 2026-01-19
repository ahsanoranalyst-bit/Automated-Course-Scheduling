import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Configuration
st.set_page_config(page_title="GEA Timetable ERP", layout="wide")

# 2. Security & Expiry (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31" 

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    # Check Expiry
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error("❌ LICENSE EXPIRED! Contact Admin.")
        return False

    if not st.session_state['authenticated']:
        st.title("🔐 System Activation")
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
                text = str(df[col][i]).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(w, 10, text, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# 4. Main Application
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Enterprise Resource Planning (ERP) System")

    with st.sidebar:
        st.header("⚙️ Settings")
        days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("Start Time", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("End Time", datetime.strptime("14:00", "%H:%M"))
        period_dur = st.number_input("Period (Mins)", 10, 120, 40)
        st.divider()
        after_p = st.number_input("Break After Period", 1, 10, 4)
        break_dur = st.number_input("Break Duration", 10, 60, 30)

    # Data Input Tabs
    st.header("🏛️ Section Management")
    tab1, tab2, tab3 = st.tabs(["Primary", "Secondary", "College"])
    
    def get_section_data(key, def_c):
        c1, c2 = st.columns([1, 2])
        classes = [c.strip() for c in c1.text_area(f"Classes List", def_c, key=f"cls_{key}").split(",") if c.strip()]
        df_edit = c2.data_editor(pd.DataFrame([{"Teacher": "", "Subject": ""}] * 5), num_rows="dynamic", key=f"t_{key}")
        teachers = [f"{r['Teacher']} ({r['Subject']})" for _, r in df_edit.iterrows() if r["Teacher"]]
        return classes, teachers

    p_c, p_t = tab1.get_section_data("pri", "Grade 1, Grade 2, Grade 3")
    s_c, s_t = tab2.get_section_data("sec", "Grade 9, Grade 10")
    c_c, c_t = tab3.get_section_data("coll", "FSc-1, FSc-2")

    if st.button("🚀 Generate & Analyze Timetables"):
        # Time Slots Generation
        time_slots = []
        curr = datetime.combine(datetime.today(), school_start)
        closing = datetime.combine(datetime.today(), school_end)
        p_idx = 1
        while curr + timedelta(minutes=period_dur) <= closing:
            ts = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=period_dur)).strftime('%I:%M %p')}"
            time_slots.append({"label": f"P{p_idx}", "time": ts, "is_break": False})
            curr += timedelta(minutes=period_dur)
            if p_idx == after_p and curr + timedelta(minutes=break_dur) <= closing:
                ts_b = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=break_dur)).strftime('%I:%M %p')}"
                time_slots.append({"label": "BREAK", "time": ts_b, "is_break": True})
                curr += timedelta(minutes=break_dur)
            p_idx += 1

        if time_slots:
            master_schedule = {} # (day, time, teacher) -> class
            taught_today = {} # (day, class) -> list of teachers
            total_slots = 0
            filled_slots = 0
            sections = [{"n": "Primary", "c": p_c, "t": p_t}, {"n": "Secondary", "c": s_c, "t": s_t}, {"n": "College", "c": c_c, "t": c_t}]

            # Logic Engine (Generate Data First)
            class_results = {}
            for sec in sections:
                for cls in sec["c"]:
                    cls_plan = {}
                    for day in days:
                        day_list = []
                        for slot in time_slots:
                            if slot["is_break"]: day_list.append("☕ BREAK")
                            else:
                                total_slots += 1
                                if (day, cls) not in taught_today: taught_today[(day, cls)] = []
                                # Filter: Free + No-Repeat
                                avail = [t for t in sec["t"] if (day, slot["time"], t) not in master_schedule and t not in taught_today[(day, cls)]]
                                if avail:
                                    choice = random.choice(avail)
                                    master_schedule[(day, slot["time"], choice)] = cls
                                    taught_today[(day, cls)].append(choice)
                                    day_list.append(choice)
                                    filled_slots += 1
                                else: day_list.append("❌ VACANT")
                        cls_plan[day] = day_list
                    class_results[cls] = pd.DataFrame(cls_plan, index=[s['time'] for s in time_slots])

            # --- DISPLAY SECTION 1: PROFIT ANALYSIS (TOP) ---
            st.markdown("---")
            st.header("📊 SECTION 1: PROFIT & EFFICIENCY ANALYSIS")
            m1, m2, m3 = st.columns(3)
            efficiency = (filled_slots / total_slots) * 100 if total_slots > 0 else 0
            m1.metric("School Efficiency Level", f"{efficiency:.1f}%")
            m2.metric("Unfilled Slots (Lost Profit)", total_slots - filled_slots)
            m3.metric("System Status", "Optimized" if efficiency > 85 else "Action Required", delta_color="normal")

            # --- DISPLAY SECTION 2: CLASS WISE TIMETABLES (MIDDLE) ---
            st.markdown("---")
            st.header("📋 SECTION 2: CLASS-WISE TIMETABLES")
            for cls, df in class_results.items():
                st.write(f"### Timetable for {cls}")
                st.table(df)
                pdf_c = create_pdf("GEA", f"Class: {cls}", df)
                st.download_button(f"📥 Download {cls} PDF", pdf_c, f"{cls}.pdf", key=f"btn_{cls}")

            # --- DISPLAY SECTION 3: TEACHER DUTY CHARTS (BOTTOM) ---
            st.markdown("---")
            st.header("👨‍🏫 SECTION 3: TEACHER DUTY CHARTS")
            all_teachers = p_t + s_t + c_t
            for t in all_teachers:
                t_plan = {}
                for day in days:
                    t_day = []
                    for slot in time_slots:
                        if slot["is_break"]: t_day.append("BREAK")
                        else: t_day.append(master_schedule.get((day, slot["time"], t), "FREE"))
                    t_plan[day] = t_day
                
                df_t = pd.DataFrame(t_plan, index=[s['time'] for s in time_slots])
                with st.expander(f"View Duty Chart: {t}"):
                    st.table(df_t)
                    pdf_t = create_pdf("GEA", f"Teacher: {t}", df_t)
                    st.download_button(f"📥 Download {t} PDF", pdf_t, f"Teacher_{t}.pdf", key=f"tbtn_{t}")
