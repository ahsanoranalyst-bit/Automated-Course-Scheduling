import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF
import io

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
        st.title("🔐 Enterprise Software Activation")
        user_key = st.text_input("Enter Activation Key:", type="password")
        if st.button("Activate"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Invalid Key")
        return False
    return True

# 3. Enhanced PDF Generator (Supports Branding & Content)
def create_pdf(school_name, header, sub, df):
    try:
        pdf = FPDF()
        pdf.add_page()
        # School Branding
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(190, 15, str(school_name).upper(), ln=True, align='C')
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, str(header), ln=True, align='C')
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(190, 8, str(sub), ln=True, align='C')
        pdf.ln(10)
        
        # Table Header
        pdf.set_font("Arial", 'B', 9)
        cols = ["Time Slot"] + list(df.columns)
        w = 190 / len(cols)
        for col in cols: pdf.cell(w, 10, str(col), 1, 0, 'C')
        pdf.ln()
        
        # Table Data
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
    # Sidebar: Branding & Global Settings
    with st.sidebar:
        st.header("🏫 School Setup")
        custom_school_name = st.text_input("Enter School Name:", "Global Excellence Academy")
        st.divider()
        st.header("⚙️ Timing Control")
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_t = st.time_input("Open", datetime.strptime("08:00", "%H:%M"))
        end_t = st.time_input("Close", datetime.strptime("14:00", "%H:%M"))
        p_mins = st.number_input("Period Duration", 10, 120, 40)
        brk_after = st.number_input("Break After Period", 1, 10, 4)
        brk_mins = st.number_input("Break Mins", 10, 60, 30)

    st.title(f"🏛️ {custom_school_name}")
    st.header("Registration & Section Manager")

    # Fixed Tab Implementation to avoid StreamlitAPIException
    tab1, tab2, tab3 = st.tabs(["Primary", "Secondary", "College"])
    
    def get_data(key, def_cls):
        c1, c2 = st.columns([1, 2])
        c_df = c1.data_editor(pd.DataFrame([{"Class": def_cls, "Sections": 1}]), num_rows="dynamic", key=f"c_{key}")
        t_df = c2.data_editor(pd.DataFrame([{"Name": "", "Subject": ""}] * 5), num_rows="dynamic", key=f"t_{key}")
        
        final_c = []
        for _, r in c_df.iterrows():
            if r["Class"]:
                for i in range(int(r["Sections"])):
                    final_c.append(f"{r['Class']} (Sec {i+1})")
        final_t = [f"{r['Name']} ({r['Subject']})" for _, r in t_df.iterrows() if r["Name"]]
        return final_c, final_t

    with tab1: p_cls, p_tea = get_data("pri", "Grade 1")
    with tab2: s_cls, s_tea = get_data("sec", "Grade 9")
    with tab3: c_cls, c_tea = get_data("col", "FSc-1")

    if st.button("🚀 Run Analysis & Print Results"):
        # Generate Time Slots
        slots = []
        curr = datetime.combine(datetime.today(), start_t)
        limit = datetime.combine(datetime.today(), end_t)
        p_idx = 1
        while curr + timedelta(minutes=p_mins) <= limit:
            t_str = f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=p_mins)).strftime('%I:%M %p')}"
            slots.append({"time": t_str, "brk": False})
            curr += timedelta(minutes=p_mins)
            if p_idx == brk_after and curr + timedelta(minutes=brk_mins) <= limit:
                slots.append({"time": f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=brk_mins)).strftime('%I:%M %p')}", "brk": True})
                curr += timedelta(minutes=brk_mins)
            p_idx += 1

        if slots:
            master = {}; class_schedules = {}; stats = {"Primary": {"T":0, "F":0}, "Secondary": {"T":0, "F":0}, "College": {"T":0, "F":0}}
            all_sections = [{"id": "Primary", "c": p_cls, "t": p_tea}, {"id": "Secondary", "c": s_cls, "t": s_tea}, {"id": "College", "c": c_cls, "t": c_tea}]

            for sec in all_sections:
                for cls in sec["c"]:
                    day_plans = {}
                    for d in days:
                        slot_list = []
                        for s in slots:
                            if s["brk"]: slot_list.append("☕ BREAK")
                            else:
                                stats[sec["id"]]["T"] += 1
                                avail = [t for t in sec["t"] if (d, s["time"], t) not in master and (d, cls, t) not in master]
                                if avail:
                                    pk = random.choice(avail)
                                    master[(d, s["time"], pk)] = cls
                                    master[(d, cls, pk)] = True
                                    slot_list.append(pk); stats[sec["id"]]["F"] += 1
                                else: slot_list.append("❌ NO STAFF")
                        day_plans[d] = slot_list
                    class_schedules[cls] = pd.DataFrame(day_plans, index=[s['time'] for s in slots])

            # --- DISPLAY 1: ANALYTICS (TOP) ---
            st.markdown("---")
            st.header(f"📊 {custom_school_name}: Profit & Efficiency Analysis")
            m1, m2, m3 = st.columns(3)
            all_f = sum(x["F"] for x in stats.values()); all_t = sum(x["T"] for x in stats.values())
            overall_eff = (all_f / all_t * 100) if all_t > 0 else 0
            m1.metric("Overall Efficiency", f"{overall_eff:.1f}%")
            m2.metric("Total Active Sections", len(class_schedules))
            m3.metric("Profit Status", "Optimized" if overall_eff > 85 else "Action Required")

            # One Line Sectional Stats (As requested)
            st.write("#### ⚡ Section Performance Statistics")
            sc1, sc2, sc3 = st.columns(3)
            for i, name in enumerate(["Primary", "Secondary", "College"]):
                eff = (stats[name]["F"] / stats[name]["T"] * 100) if stats[name]["T"] > 0 else 0
                st.columns(3)[i].info(f"**{name.upper()}**\n\nEfficiency: {eff:.1f}%\nVacancies: {stats[name]['T']-stats[name]['F']}")

            # --- DISPLAY 2: CLASS SCHEDULES ---
            st.markdown("---")
            st.header("📋 Student Class Schedules")
            for cls_name, df in class_schedules.items():
                with st.expander(f"View: {cls_name}"):
                    st.table(df)
                    pdf = create_pdf(custom_school_name, "STUDENT TIMETABLE", f"Class: {cls_name}", df)
                    if pdf: st.download_button(f"📥 Print {cls_name} PDF", pdf, f"{cls_name}.pdf", "application/pdf", key=f"btn_{cls_name}")

            # --- DISPLAY 3: TEACHER DUTIES ---
            st.markdown("---")
            st.header("👨‍🏫 Teacher Duty Charts")
            for t in (p_tea + s_tea + c_tea):
                t_duty = {d: [master.get((d, s["time"], t), "FREE") if not s["brk"] else "BREAK" for s in slots] for d in days}
                df_t = pd.DataFrame(t_duty, index=[s['time'] for s in slots])
                with st.expander(f"View: {t}"):
                    st.table(df_t)
                    t_pdf = create_pdf(custom_school_name, "TEACHER DUTY CHART", f"Teacher: {t}", df_t)
                    if t_pdf: st.download_button(f"📥 Print {t} PDF", t_pdf, f"{t}.pdf", "application/pdf", key=f"tbtn_{t}")
