import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Configuration
st.set_page_config(page_title="GEA Timetable ERP", layout="wide")

# 2. Security (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31" 

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    # Expiry Check
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error("❌ LICENSE EXPIRED! Please contact administrator.")
        return False

    if not st.session_state['authenticated']:
        st.title("🔐 Enterprise System Activation")
        user_key = st.text_input("Enter Master License Key:", type="password")
        if st.button("Activate"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.rerun()
            else: st.error("Invalid Key")
        return False
    return True

# 3. Robust PDF Generator (Fixed Encoding Error)
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
                # Fixing the 'latin-1' error by replacing incompatible characters
                val = str(df[col][i]).encode('ascii', 'ignore').decode('ascii')
                pdf.cell(w, 10, val, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S')
    except Exception as e:
        return None

# 4. App Main Logic
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Smart ERP & Profit Optimization Dashboard")

    # --- SIDEBAR SETTINGS ---
    with st.sidebar:
        st.header("⚙️ Global Settings")
        work_days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_t = st.time_input("School Opening", datetime.strptime("08:00", "%H:%M"))
        end_t = st.time_input("School Closing", datetime.strptime("14:00", "%H:%M"))
        p_duration = st.number_input("Period Mins", 10, 120, 40)
        st.divider()
        break_after = st.number_input("Break After Period", 1, 10, 4)
        break_mins = st.number_input("Break Length", 10, 60, 30)

    # --- DATA ENTRY SECTIONS (Fixed API Error) ---
    st.header("🏛️ Section Management")
    t_pri, t_sec, t_coll = st.tabs(["Primary", "Secondary", "College"])
    
    # Primary Data
    with t_pri:
        c1, c2 = st.columns([1, 2])
        p_cl_raw = c1.text_area("Primary Classes", "Grade 1, Grade 2, Grade 3", key="p_cl")
        p_cl_list = [c.strip() for c in p_cl_raw.split(",") if c.strip()]
        p_t_edit = c2.data_editor(pd.DataFrame([{"Teacher": "", "Subject": ""}] * 5), num_rows="dynamic", key="p_t_data")
        p_t_list = [f"{r['Teacher']} ({r['Subject']})" for _, r in p_t_edit.iterrows() if r["Teacher"]]

    # Secondary Data
    with t_sec:
        c1, c2 = st.columns([1, 2])
        s_cl_raw = c1.text_area("Secondary Classes", "Grade 9, Grade 10", key="s_cl")
        s_cl_list = [c.strip() for c in s_cl_raw.split(",") if c.strip()]
        s_t_edit = c2.data_editor(pd.DataFrame([{"Teacher": "", "Subject": ""}] * 5), num_rows="dynamic", key="s_t_data")
        s_t_list = [f"{r['Teacher']} ({r['Subject']})" for _, r in s_t_edit.iterrows() if r["Teacher"]]

    # College Data
    with t_coll:
        c1, c2 = st.columns([1, 2])
        col_cl_raw = c1.text_area("College Classes", "FSc-1, FSc-2", key="col_cl")
        col_cl_list = [c.strip() for c in col_cl_raw.split(",") if c.strip()]
        col_t_edit = c2.data_editor(pd.DataFrame([{"Teacher": "", "Subject": ""}] * 5), num_rows="dynamic", key="col_t_data")
        col_t_list = [f"{r['Teacher']} ({r['Subject']})" for _, r in col_edit.iterrows() if r["Teacher"]] if 'col_edit' in locals() else [] # Safety check
        # Fixed logic for college list
        col_t_list = [f"{r['Teacher']} ({r['Subject']})" for _, r in col_t_edit.iterrows() if r["Teacher"]]

    # --- ACTION BUTTON ---
    if st.button("🚀 Generate Everything & Analyze Profit"):
        # 1. Generate Time Slots
        slots = []
        curr = datetime.combine(datetime.today(), start_t)
        limit = datetime.combine(datetime.today(), end_t)
        p_idx = 1
        while curr + timedelta(minutes=p_duration) <= limit:
            time_range = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=p_duration)).strftime('%I:%M %p')}"
            slots.append({"label": f"P{p_idx}", "time": time_range, "break": False})
            curr += timedelta(minutes=p_duration)
            if p_idx == break_after and curr + timedelta(minutes=break_mins) <= limit:
                b_range = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=break_mins)).strftime('%I:%M %p')}"
                slots.append({"label": "BREAK", "time": b_range, "break": True})
                curr += timedelta(minutes=break_mins)
            p_idx += 1

        if not slots:
            st.error("Time range too short!")
        else:
            # 2. Scheduling Engine
            master_map = {} # (day, time, teacher) -> class
            class_map = {} # class -> {day: [teachers]}
            taught_count = {} # (day, class, teacher) -> bool
            total_req = 0; filled = 0
            
            sections = [
                {"name": "Primary", "classes": p_cl_list, "teachers": p_t_list},
                {"name": "Secondary", "classes": s_cl_list, "teachers": s_t_list},
                {"name": "College", "classes": col_cl_list, "teachers": col_t_list}
            ]

            for sec in sections:
                for cls in sec["classes"]:
                    day_data = {}
                    for d in work_days:
                        p_list = []
                        for s in slots:
                            if s["break"]: p_list.append("☕ BREAK")
                            else:
                                total_req += 1
                                # No-Repeat + No-Clash Logic
                                avail = [t for t in sec["teachers"] if (d, s["time"], t) not in master_map and (d, cls, t) not in taught_count]
                                if avail:
                                    pick = random.choice(avail)
                                    master_map[(d, s["time"], pick)] = cls
                                    taught_count[(d, cls, pick)] = True
                                    p_list.append(pick)
                                    filled += 1
                                else: p_list.append("❌ VACANT")
                        day_data[d] = p_list
                    class_map[cls] = pd.DataFrame(day_data, index=[s['time'] for s in slots])

            # --- DISPLAY 1: PROFIT ANALYSIS (TOP) ---
            st.markdown("---")
            st.header("📈 SECTION 1: PROFIT & EFFICIENCY LEVEL")
            score = (filled / total_req) * 100 if total_req > 0 else 0
            m1, m2, m3 = st.columns(3)
            m1.metric("School Efficiency", f"{score:.1f}%")
            m2.metric("Empty Slots (Loss)", total_req - filled)
            m3.metric("Profit Status", "Level 200 Optimized" if score > 90 else "Hiring Needed", delta_color="normal")

            # --- DISPLAY 2: CLASS TIMETABLES (MIDDLE) ---
            st.markdown("---")
            st.header("📋 SECTION 2: CLASS-WISE TIMETABLES")
            for cls, df in class_map.items():
                st.subheader(f"Timetable: {cls}")
                st.table(df)
                pdf_bytes = create_pdf("GEA ERP", f"Class Schedule: {cls}", df)
                if pdf_bytes: st.download_button(f"📥 Download {cls} PDF", pdf_bytes, f"{cls}.pdf", key=f"dl_{cls}")

            # --- DISPLAY 3: TEACHER DUTY CHARTS (BOTTOM) ---
            st.markdown("---")
            st.header("👨‍🏫 SECTION 3: TEACHER DUTY CHARTS")
            all_t = p_t_list + s_t_list + col_t_list
            for t in all_t:
                t_plan = {}
                for d in work_days:
                    row = []
                    for s in slots:
                        if s["break"]: row.append("BREAK")
                        else: row.append(master_map.get((d, s["time"], t), "FREE"))
                    t_plan[d] = row
                df_t = pd.DataFrame(t_plan, index=[s['time'] for s in slots])
                with st.expander(f"Duty Chart: {t}"):
                    st.table(df_t)
                    t_pdf = create_pdf("GEA ERP", f"Teacher Duty: {t}", df_t)
                    if t_pdf: st.download_button(f"📥 Download {t} PDF", t_pdf, f"Teacher_{t}.pdf", key=f"t_{t}")
