import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Configuration
st.set_page_config(page_title="GEA Timetable ERP", layout="wide")

# 2. Security & Software Lock (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31" 

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    # Expiry Check
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error("❌ LICENSE EXPIRED! Please contact the developer.")
        return False

    if not st.session_state['authenticated']:
        st.title("🔐 Software Activation")
        user_input = st.text_input("Enter License Key:", type="password")
        if st.button("Activate System"):
            if user_input == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Invalid Key.")
        return False
    return True

# 3. Robust PDF Function (Fixed Latin-1 Errors)
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
        for col in cols:
            pdf.cell(w, 10, str(col), 1, 0, 'C')
        pdf.ln()
        
        pdf.set_font("Arial", '', 7)
        for i in range(len(df)):
            pdf.cell(w, 10, str(df.index[i]), 1, 0, 'C')
            for col in df.columns:
                # Cleaning text for PDF
                safe_text = str(df[col][i]).encode('ascii', 'ignore').decode('ascii')
                pdf.cell(w, 10, safe_text, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S')
    except:
        return None

# 4. Main Application
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Enterprise Resource Planning & Multi-Section Manager")

    # --- Sidebar Settings ---
    with st.sidebar:
        st.header("⚙️ General Settings")
        days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_t = st.time_input("School Start", datetime.strptime("08:00", "%H:%M"))
        end_t = st.time_input("School End", datetime.strptime("14:00", "%H:%M"))
        p_mins = st.number_input("Period Duration", 10, 120, 40)
        st.divider()
        brk_after = st.number_input("Break After Period", 1, 10, 4)
        brk_mins = st.number_input("Break Duration", 10, 60, 30)

    # --- Data Input Sections ---
    st.header("🏛️ Class & Staff Registration")
    tab1, tab2, tab3 = st.tabs(["Primary Section", "Secondary Section", "College Section"])
    
    def render_section_ui(key, def_data):
        st.write(f"### {key} Setup")
        c1, c2 = st.columns([1, 2])
        # Room/Section Data Editor
        cls_df = c1.data_editor(pd.DataFrame(def_data), num_rows="dynamic", key=f"cls_edt_{key}")
        # Teacher Data Editor
        st.write("Assign Faculty:")
        tea_df = c2.data_editor(pd.DataFrame([{"Name": "", "Subject": ""}] * 5), num_rows="dynamic", key=f"tea_edt_{key}")
        
        # Processed Lists
        final_cls = []
        for _, row in cls_df.iterrows():
            if row["Class"]:
                for r in range(int(row["Sections"])):
                    final_cls.append(f"{row['Class']} (Sec {r+1})")
        
        final_tea = [f"{r['Name']} ({r['Subject']})" for _, r in tea_df.iterrows() if r["Name"]]
        return final_cls, final_tea

    with tab1: p_cls, p_tea = render_section_ui("Primary", [{"Class": "Nursery", "Sections": 1}, {"Class": "Grade 1", "Sections": 1}])
    with tab2: s_cls, s_tea = render_section_ui("Secondary", [{"Class": "Grade 9", "Sections": 1}, {"Class": "Grade 10", "Sections": 1}])
    with tab3: c_cls, c_tea = render_section_ui("College", [{"Class": "FSc-I", "Sections": 1}, {"Class": "BS-CS", "Sections": 1}])

    # --- Final Generation ---
    if st.button("🚀 Generate Optimized Schedule & Analytics"):
        # 1. Create Time Slots
        slots = []
        curr = datetime.combine(datetime.today(), start_t)
        limit = datetime.combine(datetime.today(), end_t)
        p_count = 1
        while curr + timedelta(minutes=p_mins) <= limit:
            t_str = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=p_mins)).strftime('%I:%M %p')}"
            slots.append({"time": t_str, "is_break": False})
            curr += timedelta(minutes=p_mins)
            if p_count == brk_after and curr + timedelta(minutes=brk_mins) <= limit:
                b_str = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=brk_mins)).strftime('%I:%M %p')}"
                slots.append({"time": b_str, "is_break": True})
                curr += timedelta(minutes=brk_mins)
            p_count += 1

        if not slots:
            st.error("Invalid timing settings.")
        else:
            # 2. Advanced Scheduling Engine
            master_reg = {} # (day, time, teacher) -> class
            class_schedules = {}
            stats = {"Primary": {"T":0, "F":0}, "Secondary": {"T":0, "F":0}, "College": {"T":0, "F":0}}
            
            sections = [
                {"id": "Primary", "c": p_cls, "t": p_tea},
                {"id": "Secondary", "c": s_cls, "t": s_tea},
                {"id": "College", "c": c_cls, "t": c_tea}
            ]

            for sec in sections:
                for cls in sec["c"]:
                    day_plans = {}
                    for d in days:
                        slot_list = []
                        for s in slots:
                            if s["is_break"]:
                                slot_list.append("☕ BREAK")
                            else:
                                stats[sec["id"]]["T"] += 1
                                # Logic: Teacher is free at this time AND hasn't taught this specific class today
                                avail = [t for t in sec["t"] if (d, s["time"], t) not in master_reg and (d, cls, t) not in master_reg]
                                if avail:
                                    pick = random.choice(avail)
                                    master_reg[(d, s["time"], pick)] = cls
                                    master_reg[(d, cls, pick)] = True # Mark as taught today
                                    slot_list.append(pick)
                                    stats[sec["id"]]["F"] += 1
                                else:
                                    slot_list.append("❌ NO STAFF")
                        day_plans[d] = slot_list
                    class_schedules[cls] = pd.DataFrame(day_plans, index=[s['time'] for s in slots])

            # --- DISPLAY 1: PROFIT & ANALYTICS (TOP) ---
            st.markdown("---")
            st.header("📊 SECTION 1: SYSTEM EFFICIENCY & PROFIT ANALYSIS")
            m1, m2, m3 = st.columns(3)
            
            total_f = sum(x["F"] for x in stats.values())
            total_t = sum(x["T"] for x in stats.values())
            overall_eff = (total_f / total_t * 100) if total_t > 0 else 0
            
            m1.metric("Overall School Efficiency", f"{overall_eff:.1f}%")
            m2.metric("Active Classroom Sections", len(class_schedules))
            m3.metric("Expansion Opportunity", "High" if overall_eff > 90 else "Low Staffing")

            # Sectional Breakup
            st.write("#### Section Performance Statistics")
            sc1, sc2, sc3 = st.columns(3)
            for i, (name, data) in enumerate(stats.items()):
                s_eff = (data["F"] / data["T"] * 100) if data["T"] > 0 else 0
                st.columns(3)[i].info(f"**{name} Section**\n\nEfficiency: {s_eff:.1f}%\n\nVacancies: {data['T']-data['F']}")

            # --- DISPLAY 2: CLASS TIMETABLES (MIDDLE) ---
            st.markdown("---")
            st.header("📋 SECTION 2: CLASS & SECTION TIMETABLES")
            for cls_name, df in class_schedules.items():
                with st.expander(f"Schedule: {cls_name}"):
                    st.table(df)
                    pdf_data = create_pdf("Global Excellence Academy", f"Class Schedule: {cls_name}", df)
                    if pdf_data: st.download_button(f"📥 Download {cls_name} PDF", pdf_data, f"{cls_name}.pdf", key=f"btn_{cls_name}")

            # --- DISPLAY 3: TEACHER DUTY CHARTS (BOTTOM) ---
            st.markdown("---")
            st.header("👨‍🏫 SECTION 3: TEACHER DUTY CHARTS")
            for t in (p_tea + s_tea + c_tea):
                t_duty = {d: [master_reg.get((d, s["time"], t), "FREE") if not s["is_break"] else "BREAK" for s in slots] for d in days}
                with st.expander(f"Duty Chart: {t}"):
                    df_t = pd.DataFrame(t_duty, index=[s['time'] for s in slots])
                    st.table(df_t)
                    t_pdf = create_pdf("GEA", f"Teacher Duty: {t}", df_t)
                    if t_pdf: st.download_button(f"📥 Download {t} PDF", t_pdf, f"Teacher_{t}.pdf", key=f"tbtn_{t}")
