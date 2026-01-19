import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Configuration
st.set_page_config(page_title="GEA Timetable ERP - Profit Tracker", layout="wide")

# 2. Advanced Security (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31" 

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    current_date = datetime.now().date()
    expiry = datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date()
    if current_date > expiry:
        st.error("❌ SYSTEM LOCKED: LICENSE EXPIRED!")
        return False
    if not st.session_state['authenticated']:
        st.title("🔐 Enterprise Activation")
        user_key = st.text_input("Enter License Key:", type="password")
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

# 4. Main ERP Application
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Smart ERP & Resource Optimization Dashboard")

    with st.sidebar:
        st.header("⚙️ Schedule Settings")
        days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        school_start = st.time_input("Start Time", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("Closing Time", datetime.strptime("14:00", "%H:%M"))
        period_dur = st.number_input("Period (Mins)", 10, 120, 40)
        st.divider()
        after_p = st.number_input("Break After Period", 1, 10, 4)
        break_dur = st.number_input("Break Length", 10, 60, 30)

    st.markdown("### 🏛️ Faculty & Classes")
    tab1, tab2, tab3 = st.tabs(["Primary", "Secondary", "College"])

    def manage_sec(key_id, default_cls):
        c1, c2 = st.columns([1, 2])
        cls_list = [c.strip() for c in c1.text_area(f"Classes", default_cls, key=f"c_{key_id}").split(",") if c.strip()]
        st.write(f"Assign Teachers:")
        df_in = pd.DataFrame([{"Teacher Name": "", "Subject": ""}] * 5)
        edited = c2.data_editor(df_in, num_rows="dynamic", key=f"t_{key_id}")
        teachers = [f"{r['Teacher Name']} ({r['Subject']})" for _, r in edited.iterrows() if r["Teacher Name"]]
        return cls_list, teachers

    p_cls, p_tea = manage_sec("pri", "Grade 1, Grade 2")
    s_cls, s_tea = manage_sec("sec", "Grade 9, Grade 10")
    c_cls, c_tea = manage_sec("coll", "FSc-1, FSc-2")

    if st.button("🚀 Generate Schedule & Analyze Profit"):
        # 1. Time Logic
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
            master_reg = {}; taught_today = {}; sections = [{"name": "Primary", "c": p_cls, "t": p_tea}, {"name": "Secondary", "c": s_cls, "t": s_tea}, {"name": "College", "c": c_cls, "t": c_tea}]
            
            # Tracking Stats for Profit Analysis
            total_slots = 0; filled_slots = 0; teacher_workload = {t: 0 for t in (p_tea + s_tea + c_tea)}

            st.header("📋 CLASS TIMETABLES")
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
                                avail = [t for t in sec["t"] if (day, slot["time"], t) not in master_reg and t not in taught_today[(day, cls)]]
                                if avail:
                                    choice = random.choice(avail)
                                    master_reg[(day, slot["time"], choice)] = cls
                                    taught_today[(day, cls)].append(choice)
                                    day_list.append(choice)
                                    filled_slots += 1; teacher_workload[choice] += 1
                                else: day_list.append("❌ VACANT SLOT")
                        cls_plan[day] = day_list
                    st.write(f"**Class: {cls}**"); st.table(pd.DataFrame(cls_plan, index=[s['time'] for s in time_slots]))

            # --- PROFIT & RESOURCE ANALYSIS DASHBOARD ---
            st.divider()
            st.header("📈 Resource Optimization Dashboard (Profit Level 200)")
            m1, m2, m3 = st.columns(3)
            
            utilization = (filled_slots / total_slots) * 100 if total_slots > 0 else 0
            m1.metric("Classroom Efficiency", f"{utilization:.1f}%", help="Percentage of periods successfully covered by staff.")
            
            vacancies = total_slots - filled_slots
            m2.metric("Unfilled Slots (Warning)", vacancies, delta="- New Hiring Needed" if vacancies > 0 else "Fully Optimized", delta_color="inverse")
            
            # Teacher Load Analysis
            st.write("### 👨‍🏫 Teacher Workload (Total Periods per Week)")
            load_df = pd.DataFrame(list(teacher_workload.items()), columns=['Teacher', 'Total Periods'])
            st.bar_chart(load_df.set_index('Teacher'))

            # Teacher Duty PDF
            st.header("👨‍🏫 Teacher Duty Charts")
            for t in (p_tea + s_tea + c_tea):
                t_plan = {day: [master_reg.get((day, slot["time"], t), "FREE" if not slot["is_break"] else "BREAK") for slot in time_slots] for day in days}
                with st.expander(f"Duty Chart: {t}"):
                    df_t = pd.DataFrame(t_plan, index=[s['time'] for s in time_slots]); st.table(df_t)
                    pdf = create_pdf("GEA", f"Teacher: {t}", df_t)
                    st.download_button(f"Download {t} PDF", pdf, f"{t}.pdf", key=f"p_{t}")
