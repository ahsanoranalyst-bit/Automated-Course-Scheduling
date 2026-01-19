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
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error("❌ LICENSE EXPIRED!")
        return False
    if not st.session_state['authenticated']:
        st.title("🔐 Enterprise System Activation")
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
        pdf.set_font("Arial", 'B', 8)
        cols = ["Time Slot"] + list(df.columns)
        w = 190 / len(cols)
        for col in cols: pdf.cell(w, 10, str(col), 1, 0, 'C')
        pdf.ln()
        pdf.set_font("Arial", '', 7)
        for i in range(len(df)):
            pdf.cell(w, 10, str(df.index[i]), 1, 0, 'C')
            for col in df.columns:
                val = str(df[col][i]).encode('ascii', 'ignore').decode('ascii')
                pdf.cell(w, 10, val, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S')
    except: return None

# 4. App Logic
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("ERP with Sectional Profit Analytics")

    with st.sidebar:
        st.header("⚙️ Settings")
        work_days = st.multiselect("Working Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        start_t = st.time_input("Opening", datetime.strptime("08:00", "%H:%M"))
        end_t = st.time_input("Closing", datetime.strptime("14:00", "%H:%M"))
        p_dur = st.number_input("Period Mins", 10, 120, 40)
        break_after = st.number_input("Break After Period", 1, 10, 4)
        break_mins = st.number_input("Break Length", 10, 60, 30)

    st.header("🏛️ Data Entry")
    t1, t2, t3 = st.tabs(["Primary", "Secondary", "College"])
    
    with t1:
        c1, c2 = st.columns([1, 2])
        p_cls = [c.strip() for c in c1.text_area("Primary Classes", "Grade 1, Grade 2", key="p_cl").split(",") if c.strip()]
        p_tea_df = c2.data_editor(pd.DataFrame([{"Teacher": "", "Subject": ""}] * 5), num_rows="dynamic", key="p_t_ed")
        p_tea = [f"{r['Teacher']} ({r['Subject']})" for _, r in p_tea_df.iterrows() if r["Teacher"]]

    with t2:
        c1, c2 = st.columns([1, 2])
        s_cls = [c.strip() for c in c1.text_area("Secondary Classes", "Grade 9, Grade 10", key="s_cl").split(",") if c.strip()]
        s_tea_df = c2.data_editor(pd.DataFrame([{"Teacher": "", "Subject": ""}] * 5), num_rows="dynamic", key="s_t_ed")
        s_tea = [f"{r['Teacher']} ({r['Subject']})" for _, r in s_tea_df.iterrows() if r["Teacher"]]

    with t3:
        c1, c2 = st.columns([1, 2])
        col_cls = [c.strip() for c in c1.text_area("College Classes", "FSc-1, FSc-2", key="col_cl").split(",") if c.strip()]
        col_tea_df = c2.data_editor(pd.DataFrame([{"Teacher": "", "Subject": ""}] * 5), num_rows="dynamic", key="col_t_ed")
        col_tea = [f"{r['Teacher']} ({r['Subject']})" for _, r in col_tea_df.iterrows() if r["Teacher"]]

    if st.button("🚀 Run Sectional Analysis & Generate Tables"):
        # Time Slots
        slots = []
        curr = datetime.combine(datetime.today(), start_t)
        limit = datetime.combine(datetime.today(), end_t)
        idx = 1
        while curr + timedelta(minutes=p_dur) <= limit:
            tr = f"{curr.strftime('%I:%M %p')}-{(curr + timedelta(minutes=p_dur)).strftime('%I:%M %p')}"
            slots.append({"t": tr, "b": False})
            curr += timedelta(minutes=p_dur)
            if idx == break_after and curr + timedelta(minutes=break_mins) <= limit:
                slots.append({"t": f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=break_mins)).strftime('%I:%M %p')}", "b": True})
                curr += timedelta(minutes=break_mins)
            idx += 1

        if slots:
            master = {}; class_results = {}; stats = {}
            sections = [
                {"id": "Primary", "c": p_cls, "t": p_tea},
                {"id": "Secondary", "c": s_cls, "t": s_tea},
                {"id": "College", "c": col_cls, "t": col_tea}
            ]

            all_total = 0; all_filled = 0

            for sec in sections:
                sec_total = 0; sec_filled = 0
                for cls in sec["c"]:
                    cls_plan = {}
                    for d in work_days:
                        day_list = []
                        for s in slots:
                            if s["b"]: day_list.append("☕ BREAK")
                            else:
                                sec_total += 1; all_total += 1
                                # No-Repeat + No-Clash Logic
                                avail = [t for t in sec["t"] if (d, s["t"], t) not in master and (d, cls, t) not in master]
                                if avail:
                                    pk = random.choice(avail)
                                    master[(d, s["t"], pk)] = cls
                                    master[(d, cls, pk)] = True # Track repeat in same class
                                    day_list.append(pk); sec_filled += 1; all_filled += 1
                                else: day_list.append("❌ VACANT")
                        cls_plan[d] = day_list
                    class_results[cls] = pd.DataFrame(cls_plan, index=[s['t'] for s in slots])
                stats[sec["id"]] = {"total": sec_total, "filled": sec_filled}

            # --- 1. SECTIONAL ANALYTICS (TOP) ---
            st.markdown("---")
            st.header("📈 SECTION 1: PROFIT & EFFICIENCY ANALYTICS")
            
            # Overall Score
            overall_eff = (all_filled / all_total) * 100 if all_total > 0 else 0
            st.metric("TOTAL SCHOOL EFFICIENCY (OVERALL)", f"{overall_eff:.1f}%")
            
            # Section Wise Columns
            m1, m2, m3 = st.columns(3)
            def show_metric(col, name, data):
                eff = (data["filled"] / data["total"]) * 100 if data["total"] > 0 else 0
                col.subheader(f"📊 {name}")
                col.write(f"Efficiency: **{eff:.1f}%**")
                col.write(f"Vacant Slots: **{data['total'] - data['filled']}**")
                if eff < 80: col.warning("Low Profit: Hiring Required")
                else: col.success("Optimized")

            show_metric(m1, "Primary", stats["Primary"])
            show_metric(m2, "Secondary", stats["Secondary"])
            show_metric(m3, "College", stats["College"])

            # --- 2. CLASS TIMETABLES (MIDDLE) ---
            st.markdown("---")
            st.header("📋 SECTION 2: CLASS TIMETABLES")
            for cls, df in class_results.items():
                st.subheader(f"Schedule: {cls}")
                st.table(df)
                p_bt = create_pdf("GEA", f"Class: {cls}", df)
                if p_bt: st.download_button(f"📥 Download {cls} PDF", p_bt, f"{cls}.pdf", key=f"d_{cls}")

            # --- 3. TEACHER DUTY CHARTS (BOTTOM) ---
            st.markdown("---")
            st.header("👨‍🏫 SECTION 3: TEACHER DUTY CHARTS")
            all_teachers = p_tea + s_tea + col_tea
            for t in all_teachers:
                t_p = {d: [master.get((d, s["t"], t), "FREE") if not s["b"] else "BREAK" for s in slots] for d in work_days}
                df_t = pd.DataFrame(t_p, index=[s['t'] for s in slots])
                with st.expander(f"View Duty: {t}"):
                    st.table(df_t)
                    pdf_t = create_pdf("GEA", f"Duty: {t}", df_t)
                    if pdf_t: st.download_button(f"📥 Download {t} PDF", pdf_t, f"{t}.pdf", key=f"t_{t}")
