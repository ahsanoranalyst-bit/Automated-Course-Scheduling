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
    st.subheader("Final ERP: Primary, Secondary & College Timetables")

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

    # --- DATA ENTRY: SEPARATE BOXES ---
    st.header("🏛️ Faculty & Classes Data Entry")
    
    # --- PRIMARY BOX ---
    with st.expander("👶 PRIMARY SECTION (Click to expand)", expanded=True):
        c1, c2 = st.columns([1, 2])
        p_classes = c1.text_area("Primary Classes", "Grade 1, Grade 2", key="p_c")
        p_list = [c.strip() for c in p_classes.split(",") if c.strip()]
        st.write("Primary Teachers & Their Subjects:")
        p_df = pd.DataFrame([{"Teacher Name": "", "Subject": ""}] * 5)
        p_edit = c2.data_editor(p_df, num_rows="dynamic", key="p_t")
        p_teachers = [f"{r['Teacher Name']} ({r['Subject']})" for _, r in p_edit.iterrows() if r["Teacher Name"]]

    # --- SECONDARY BOX ---
    with st.expander("🏫 SECONDARY SECTION (Click to expand)", expanded=False):
        c1, c2 = st.columns([1, 2])
        s_classes = c1.text_area("Secondary Classes", "Grade 9, Grade 10", key="s_c")
        s_list = [c.strip() for c in s_classes.split(",") if c.strip()]
        st.write("Secondary Teachers & Their Subjects:")
        s_df = pd.DataFrame([{"Teacher Name": "", "Subject": ""}] * 5)
        s_edit = c2.data_editor(s_df, num_rows="dynamic", key="s_t")
        s_teachers = [f"{r['Teacher Name']} ({r['Subject']})" for _, r in s_edit.iterrows() if r["Teacher Name"]]

    # --- COLLEGE BOX ---
    with st.expander("🎓 COLLEGE SECTION (Click to expand)", expanded=False):
        c1, c2 = st.columns([1, 2])
        col_classes = c1.text_area("College Classes", "FSc-1, FSc-2", key="col_c")
        col_list = [c.strip() for c in col_classes.split(",") if c.strip()]
        st.write("College Teachers & Their Subjects:")
        col_df = pd.DataFrame([{"Teacher Name": "", "Subject": ""}] * 5)
        col_edit = c2.data_editor(col_df, num_rows="dynamic", key="col_t")
        col_teachers = [f"{r['Teacher Name']} ({r['Subject']})" for _, r in col_edit.iterrows() if r["Teacher Name"]]

    # --- GENERATION ---
    if st.button("🚀 Generate All Professional Reports"):
        # Time Slots Logic
        time_slots = []
        curr = datetime.combine(datetime.today(), school_start)
        closing = datetime.combine(datetime.today(), school_end)
        p_num = 1
        while curr + timedelta(minutes=period_dur) <= closing:
            slot_t = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=period_dur)).strftime('%I:%M %p')}"
            time_slots.append({"label": f"P{p_num}", "time": slot_t, "is_break": False})
            curr += timedelta(minutes=period_dur)
            if p_num == after_p and curr + timedelta(minutes=break_dur) <= closing:
                time_slots.append({"label": "BREAK", "time": f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=break_dur)).strftime('%I:%M %p')}", "is_break": True})
                curr += timedelta(minutes=break_dur)
            p_num += 1

        if time_slots:
            master_reg = {}; taught_today = {}; sections = [
                {"name": "Primary", "c": p_list, "t": p_teachers},
                {"name": "Secondary", "c": s_list, "t": s_teachers},
                {"name": "College", "c": col_list, "t": col_teachers}
            ]
            
            # TRACKING STATS
            total_slots = 0; filled_slots = 0; teacher_load = {t: 0 for t in (p_teachers + s_teachers + col_teachers)}

            st.markdown("---")
            st.header("📋 SECTION 1: STUDENT CLASS TIMETABLES")
            for sec in sections:
                if not sec["c"]: continue
                for cls in sec["c"]:
                    cls_plan = {}
                    for day in days:
                        day_list = []
                        for slot in time_slots:
                            if slot["is_break"]: day_list.append("☕ BREAK")
                            else:
                                total_slots += 1
                                if (day, cls) not in taught_today: taught_today[(day, cls)] = []
                                # No-Repeat + Clash check
                                avail = [t for t in sec["t"] if (day, slot["time"], t) not in master_reg and t not in taught_today[(day, cls)]]
                                if avail:
                                    choice = random.choice(avail)
                                    master_reg[(day, slot["time"], choice)] = cls
                                    taught_today[(day, cls)].append(choice)
                                    day_list.append(choice)
                                    filled_slots += 1; teacher_load[choice] += 1
                                else: day_list.append("❌ NO STAFF / VACANT")
                        cls_plan[day] = day_list
                    
                    df_cls = pd.DataFrame(cls_plan, index=[s['time'] for s in time_slots])
                    st.write(f"**Class: {cls}**")
                    st.table(df_cls)
                    pdf_c = create_pdf("GEA", f"Class: {cls}", df_cls)
                    st.download_button(f"📥 Download {cls} PDF", pdf_c, f"{cls}.pdf", key=f"d_{cls}")

            st.markdown("---")
            st.header("📊 SECTION 2: PROFIT & EFFICIENCY ANALYSIS")
            m1, m2 = st.columns(2)
            eff = (filled_slots / total_slots) * 100 if total_slots > 0 else 0
            m1.metric("School Efficiency Score", f"{eff:.1f}%")
            m2.metric("Staff Vacancies Found", total_slots - filled_slots)

            st.markdown("---")
            st.header("👨‍🏫 SECTION 3: TEACHER DUTY CHARTS")
            for t in (p_teachers + s_teachers + col_teachers):
                t_plan = {day: [master_reg.get((day, slot["time"], t), "FREE" if not slot["is_break"] else "BREAK") for slot in time_slots] for day in days}
                with st.expander(f"Duty Chart: {t}"):
                    df_t = pd.DataFrame(t_plan, index=[s['time'] for s in time_slots]); st.table(df_t)
                    pdf = create_pdf("GEA", f"Teacher: {t}", df_t)
                    st.download_button(f"📥 Download {t} PDF", pdf, f"{t}.pdf", key=f"tp_{t}")
