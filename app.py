import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Config
st.set_page_config(page_title="ERP Timetable Pro", layout="wide")

# 2. Security (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31" 

def check_license():
    if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error("❌ LICENSE EXPIRED!")
        return False
    if not st.session_state['authenticated']:
        st.title("🔐 Enterprise Software Activation")
        user_key = st.text_input("Enter Activation Key:", type="password")
        if st.button("Activate"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Invalid Key")
        return False
    return True

# 3. Fixed PDF Generator with Dynamic School Name
def create_pdf(school_name, header, sub, df):
    try:
        pdf = FPDF()
        pdf.add_page()
        # School Name Header
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(190, 15, str(school_name).upper(), ln=True, align='C')
        
        # Sub Header
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, str(header), ln=True, align='C')
        pdf.set_font("Arial", 'I', 11)
        pdf.cell(190, 10, str(sub), ln=True, align='C')
        pdf.ln(10)
        
        # Table Header
        pdf.set_font("Arial", 'B', 9)
        cols = ["Time Slot"] + list(df.columns)
        w = 190 / len(cols)
        for col in cols:
            pdf.cell(w, 10, str(col), 1, 0, 'C')
        pdf.ln()
        
        # Table Body
        pdf.set_font("Arial", '', 8)
        for i in range(len(df)):
            pdf.cell(w, 10, str(df.index[i]), 1, 0, 'C')
            for col in df.columns:
                val = str(df[col][i]).encode('ascii', 'ignore').decode('ascii')
                pdf.cell(w, 10, val, 1, 0, 'C')
            pdf.ln()
            
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        return None

# 4. Main App
if check_license():
    # Sidebar Branding & Settings
    with st.sidebar:
        st.header("🏫 School Identity")
        # یہ وہ آپشن ہے جہاں ہر اسکول اپنا نام لکھے گا
        school_name = st.text_input("Enter School Name:", "Global Excellence Academy")
        st.divider()
        st.header("⚙️ Timing Settings")
        days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_t = st.time_input("School Start", datetime.strptime("08:00", "%H:%M"))
        end_t = st.time_input("School End", datetime.strptime("14:00", "%H:%M"))
        p_mins = st.number_input("Period Duration", 10, 120, 40)
        brk_after = st.number_input("Break After Period", 1, 10, 4)
        brk_mins = st.number_input("Break Duration", 10, 60, 30)

    # Main Dashboard Header
    st.title(f"🏛️ {school_name}")
    st.subheader("Smart ERP & Multi-Section Profit Dashboard")

    st.header("📋 Registration")
    tab1, tab2, tab3 = st.tabs(["Primary", "Secondary", "College"])
    
    def render_input(tab_obj, key, default_cls):
        with tab_obj:
            c1, c2 = st.columns([1, 2])
            cls_df = c1.data_editor(pd.DataFrame([{"Class": default_cls, "Rooms": 1}]), num_rows="dynamic", key=f"cls_{key}")
            tea_df = c2.data_editor(pd.DataFrame([{"Name": "", "Subject": ""}] * 5), num_rows="dynamic", key=f"tea_{key}")
            
            final_cls = []
            for _, r in cls_df.iterrows():
                if r["Class"]:
                    for i in range(int(r["Rooms"])):
                        final_cls.append(f"{row_cls := r['Class']} (Room {i+1})")
            final_tea = [f"{r['Name']} ({r['Subject']})" for _, r in tea_df.iterrows() if r["Name"]]
            return final_cls, final_tea

    p_cls, p_tea = render_input(tab1, "pri", "Grade 1")
    s_cls, s_tea = render_input(tab2, "sec", "Grade 9")
    c_cls, c_tea = render_input(tab3, "coll", "FSc-1")

    if st.button("🚀 Generate Enterprise Analysis"):
        slots = []
        curr = datetime.combine(datetime.today(), start_t)
        limit = datetime.combine(datetime.today(), end_t)
        p_idx = 1
        while curr + timedelta(minutes=p_mins) <= limit:
            t_str = f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=p_mins)).strftime('%I:%M %p')}"
            slots.append({"time": t_str, "break": False})
            curr += timedelta(minutes=p_mins)
            if p_idx == brk_after and curr + timedelta(minutes=brk_mins) <= limit:
                slots.append({"time": f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=brk_mins)).strftime('%I:%M %p')}", "break": True})
                curr += timedelta(minutes=brk_mins)
            p_idx += 1

        if slots:
            master = {}; class_schedules = {}; stats = {"Primary": {"T":0, "F":0}, "Secondary": {"T":0, "F":0}, "College": {"T":0, "F":0}}
            sections = [{"id": "Primary", "c": p_cls, "t": p_tea}, {"id": "Secondary", "c": s_cls, "t": s_tea}, {"id": "College", "c": c_cls, "t": c_tea}]

            for sec in sections:
                for cls in sec["c"]:
                    day_plans = {}
                    for d in days:
                        slot_list = []
                        for s in slots:
                            if s["break"]: slot_list.append("BREAK")
                            else:
                                stats[sec["id"]]["T"] += 1
                                avail = [t for t in sec["t"] if (d, s["time"], t) not in master and (d, cls, t) not in master]
                                if avail:
                                    pk = random.choice(avail)
                                    master[(d, s["time"], pk)] = cls
                                    master[(d, cls, pk)] = True
                                    slot_list.append(pk); stats[sec["id"]]["F"] += 1
                                else: slot_list.append("NO STAFF")
                        day_plans[d] = slot_list
                    class_schedules[cls] = pd.DataFrame(day_plans, index=[s['time'] for s in slots])

            # --- DISPLAY 1: PROFIT & SECTION PERFORMANCE (TOP) ---
            st.markdown("---")
            st.header(f"📊 {school_name}: Efficiency Analysis")
            m1, m2, m3 = st.columns(3)
            all_f = sum(x["F"] for x in stats.values()); all_t = sum(x["T"] for x in stats.values())
            overall_eff = (all_f / all_t * 100) if all_t > 0 else 0
            m1.metric("Overall Efficiency", f"{overall_eff:.1f}%")
            m2.metric("Active Rooms", len(class_schedules))
            m3.metric("Profit Status", "Optimized" if overall_eff > 90 else "Action Required")

            # One Line Section Performance
            st.write("#### ⚡ Section-Wise Performance")
            sc1, sc2, sc3 = st.columns(3)
            for i, name in enumerate(["Primary", "Secondary", "College"]):
                eff = (stats[name]["F"] / stats[name]["T"] * 100) if stats[name]["T"] > 0 else 0
                st.columns(3)[i].info(f"**{name.upper()}**\n\nEff: {eff:.1f}%\nVacancies: {stats[name]['T']-stats[name]['F']}")

            # --- DISPLAY 2: CLASS TIMETABLES (MIDDLE) ---
            st.markdown("---")
            st.header("📋 Student Timetables")
            for cls_name, df in class_schedules.items():
                with st.expander(f"Schedule: {cls_name}"):
                    st.table(df)
                    pdf_bytes = create_pdf(school_name, "STUDENT TIMETABLE", f"Class: {cls_name}", df)
                    if pdf_bytes:
                        st.download_button(f"📥 Print {cls_name} PDF", pdf_bytes, f"{cls_name}.pdf", "application/pdf", key=f"d_{cls_name}")

            # --- DISPLAY 3: TEACHER DUTY CHARTS (BOTTOM) ---
            st.markdown("---")
            st.header("👨‍🏫 Teacher Duty Charts")
            for t in (p_tea + s_tea + c_tea):
                t_duty = {d: [master.get((d, s["time"], t), "FREE") if not s["break"] else "BREAK" for s in slots] for d in days}
                df_t = pd.DataFrame(t_duty, index=[s['time'] for s in slots])
                with st.expander(f"Duty Chart: {t}"):
                    st.table(df_t)
                    t_pdf = create_pdf(school_name, "TEACHER DUTY CHART", f"Teacher: {t}", df_t)
                    if t_pdf:
                        st.download_button(f"📥 Print {t} PDF", t_pdf, f"Teacher_{t}.pdf", "application/pdf", key=f"t_{t}")
