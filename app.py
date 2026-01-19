import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Configuration
st.set_page_config(page_title="School ERP Pro", layout="wide")

# 2. Security (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31" 

def check_license():
    if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error("❌ LICENSE EXPIRED!")
        return False
    if not st.session_state['authenticated']:
        st.title("🔐 Enterprise Activation")
        user_key = st.text_input("Activation Key:", type="password")
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
        pdf = FPDF(orientation='L') 
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 15, str(school_name).upper(), ln=True, align='C')
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, str(header), ln=True, align='C')
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 8)
        cols = ["Item"] + list(df.columns)
        w = 270 / len(cols)
        for col in cols: pdf.cell(w, 10, str(col)[:15], 1, 0, 'C')
        pdf.ln()
        
        pdf.set_font("Arial", '', 7)
        for i in range(len(df)):
            pdf.cell(w, 8, str(df.index[i])[:15], 1, 0, 'C')
            for col in df.columns:
                val = str(df[col][i]).encode('ascii', 'ignore').decode('ascii')
                pdf.cell(w, 8, val[:20], 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# 4. Main ERP Logic
if check_license():
    with st.sidebar:
        st.header("🏫 Setup")
        school_name = st.text_input("School Name:", "Global Excellence Academy")
        days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_t = st.time_input("Opens", datetime.strptime("08:00", "%H:%M"))
        end_t = st.time_input("Closes", datetime.strptime("14:00", "%H:%M"))
        p_mins = st.number_input("Period Duration", 10, 120, 40)
        brk_after = st.number_input("Break After", 1, 10, 4)
        brk_mins = st.number_input("Break Duration", 10, 60, 30)

    st.title(f"🏛️ {school_name}")
    
    # Registration Tabs
    t1, t2, t3 = st.tabs(["Primary Section", "Secondary Section", "College Section"])
    with t1:
        c1, c2 = st.columns([1, 2]); p_c_df = c1.data_editor(pd.DataFrame([{"Class": "Grade 1", "Sections": 1}]), num_rows="dynamic", key="p_c")
        p_t_df = c2.data_editor(pd.DataFrame([{"Name": "", "Subject": ""}] * 5), num_rows="dynamic", key="p_t")
    with t2:
        c1, c2 = st.columns([1, 2]); s_c_df = c1.data_editor(pd.DataFrame([{"Class": "Grade 9", "Sections": 1}]), num_rows="dynamic", key="s_c")
        s_t_df = c2.data_editor(pd.DataFrame([{"Name": "", "Subject": ""}] * 5), num_rows="dynamic", key="s_t")
    with t3:
        c1, c2 = st.columns([1, 2]); c_c_df = c1.data_editor(pd.DataFrame([{"Class": "FSc-1", "Sections": 1}]), num_rows="dynamic", key="c_c")
        c_t_df = c2.data_editor(pd.DataFrame([{"Name": "", "Subject": ""}] * 5), num_rows="dynamic", key="c_t")

    if st.button("🚀 EXECUTE FULL ANALYSIS"):
        def process(c_df, t_df):
            cls = []
            for _, r in c_df.iterrows():
                if r["Class"]:
                    for i in range(int(r["Sections"])): cls.append(f"{r['Class']} (S{i+1})")
            tea = [f"{r['Name']} ({r['Subject']})" for _, r in t_df.iterrows() if r["Name"]]
            return cls, tea

        p_cls, p_tea = process(p_c_df, p_t_df); s_cls, s_tea = process(s_c_df, s_t_df); c_cls, c_tea = process(c_c_df, c_t_df)

        slots = []
        curr = datetime.combine(datetime.today(), start_t); limit = datetime.combine(datetime.today(), end_t); idx = 1
        while curr + timedelta(minutes=p_mins) <= limit:
            t_str = f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=p_mins)).strftime('%I:%M %p')}"
            slots.append({"time": t_str, "brk": False})
            curr += timedelta(minutes=p_mins)
            if idx == brk_after and curr + timedelta(minutes=brk_mins) <= limit:
                slots.append({"time": f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=brk_mins)).strftime('%I:%M %p')}", "brk": True})
                curr += timedelta(minutes=brk_mins)
            idx += 1

        master = {}; class_schedules = {}; stats = {"Primary": {"T":0, "F":0}, "Secondary": {"T":0, "F":0}, "College": {"T":0, "F":0}}
        all_sects = [{"id": "Primary", "c": p_cls, "t": p_tea}, {"id": "Secondary", "c": s_cls, "t": s_tea}, {"id": "College", "c": c_cls, "t": c_tea}]

        for sec in all_sects:
            for cls in sec["c"]:
                day_plans = {}
                for d in days:
                    slot_list = []
                    for s in slots:
                        if s["brk"]: slot_list.append("BREAK")
                        else:
                            stats[sec["id"]]["T"] += 1
                            avail = [t for t in sec["t"] if (d, s["time"], t) not in master and (d, cls, t) not in master]
                            if avail:
                                pk = random.choice(avail); master[(d, s["time"], pk)] = cls
                                master[(d, cls, pk)] = True; slot_list.append(pk); stats[sec["id"]]["F"] += 1
                            else: slot_list.append("VACANT")
                    day_plans[d] = slot_list
                class_schedules[cls] = pd.DataFrame(day_plans, index=[s['time'] for s in slots])

        # --- SECTION 1: ONE LINE PERFORMANCE ---
        st.markdown("---")
        st.header("📈 Overall School Performance")
        m1, m2, m3 = st.columns(3)
        all_f = sum(x["F"] for x in stats.values()); all_t = sum(x["T"] for x in stats.values()); eff = (all_f / all_t * 100) if all_t > 0 else 0
        m1.metric("Overall Efficiency", f"{eff:.1f}%"); m2.metric("Total Rooms", len(class_schedules)); m3.metric("Profitability", "High" if eff > 85 else "Review")

        # Fixed Row for Sections
        st.write("#### ⚡ Section Wise Stats")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            pe = (stats["Primary"]["F"]/stats["Primary"]["T"]*100) if stats["Primary"]["T"] > 0 else 0
            st.info(f"**PRIMARY**\n\nEff: {pe:.1f}%\nVacancies: {stats['Primary']['T']-stats['Primary']['F']}")
        with sc2:
            se = (stats["Secondary"]["F"]/stats["Secondary"]["T"]*100) if stats["Secondary"]["T"] > 0 else 0
            st.info(f"**SECONDARY**\n\nEff: {se:.1f}%\nVacancies: {stats['Secondary']['T']-stats['Secondary']['F']}")
        with sc3:
            ce = (stats["College"]["F"]/stats["College"]["T"]*100) if stats["College"]["T"] > 0 else 0
            st.info(f"**COLLEGE**\n\nEff: {ce:.1f}%\nVacancies: {stats['College']['T']-stats['College']['F']}")

        # --- SECTION 2: OFFICIAL TIMETABLES ---
        st.markdown("---")
        st.header("📋 Student & Teacher Official Charts")
        for cls, df in class_schedules.items():
            with st.expander(f"Class: {cls}"):
                st.table(df)
                p = create_pdf(school_name, "CLASS TIMETABLE", f"Room: {cls}", df)
                st.download_button(f"Print {cls} PDF", p, f"{cls}.pdf", key=f"b_{cls}")

        st.markdown("---")
        all_staff = p_tea + s_tea + c_tea
        for t in all_staff:
            t_duty = {d: [master.get((d, s["time"], t), "FREE") if not s["brk"] else "BREAK" for s in slots] for d in days}
            df_t = pd.DataFrame(t_duty, index=[s['time'] for s in slots])
            with st.expander(f"Teacher: {t}"):
                st.table(df_t)
                tp = create_pdf(school_name, "TEACHER DUTY", f"Staff: {t}", df_t)
                st.download_button(f"Print {t} PDF", tp, f"{t}.pdf", key=f"tea_{t}")

        # --- SECTION 3: STAFF ROOM MASTER WEEKLY SUMMARY ---
        st.markdown("---")
        st.header("🏢 STAFF ROOM MASTER SUMMARY SHEET")
        weekly_summary = []
        for t in all_staff:
            row = {"Teacher": t}
            for d in days:
                busy = [s["time"] for s in slots if not s["brk"] and (d, s["time"], t) in master]
                row[d] = f"{len(busy)} Periods" if busy else "FREE"
            weekly_summary.append(row)
        
        df_summary = pd.DataFrame(weekly_summary).set_index("Teacher")
        st.table(df_summary)
        summary_pdf = create_pdf(school_name, "WEEKLY MASTER SUMMARY", "Workload Distribution", df_summary)
        if summary_pdf:
            st.download_button("📥 DOWNLOAD MASTER SUMMARY PDF", summary_pdf, "Weekly_Summary.pdf")
