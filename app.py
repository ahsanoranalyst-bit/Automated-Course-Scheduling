import streamlit as st
import pandas as pd
import random
import json
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Configuration
st.set_page_config(page_title="Automated Course Scheduling Optimizer", layout="wide")

# 2. Database Connection (Neon)
conn = st.connection("postgresql", type="sql")

def init_db():
    """Create the table if it doesn't exist."""
    with conn.session as s:
        s.execute("""
            CREATE TABLE IF NOT EXISTS school_data (
                project_name TEXT PRIMARY KEY,
                school_name TEXT,
                config_json TEXT,
                last_updated TIMESTAMP
            );
        """)
        s.commit()

def save_to_neon(school_name, config_data):
    """Saves all UI inputs to Neon."""
    config_str = json.dumps(config_data)
    with conn.session as s:
        s.execute(
            """
            INSERT INTO school_data (project_name, school_name, config_json, last_updated)
            VALUES (:p, :s, :c, :t)
            ON CONFLICT (project_name) 
            DO UPDATE SET school_name = :s, config_json = :c, last_updated = :t
            """,
            {"p": "Automated-Course-Scheduling", "s": school_name, "c": config_str, "t": datetime.now()}
        )
        s.commit()

def load_from_neon():
    """Loads previous work from Neon."""
    df = conn.query("SELECT config_json FROM school_data WHERE project_name = 'Automated-Course-Scheduling';", ttl=0)
    if not df.empty:
        return json.loads(df.iloc[0]['config_json'])
    return None

# Initialize Database
init_db()

# 3. Security (Profit Level 200)
MASTER_KEY = "Ahsan123"
EXPIRY_DATE = "2030-12-31"

def check_license():
    if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
    if datetime.now().date() > datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date():
        st.error(" LICENSE EXPIRED!")
        return False
    if not st.session_state['authenticated']:
        st.title(" Automated Course Scheduling Optimizer Activation")
        user_key = st.text_input("Enter Activation Key:", type="password")
        if st.button("Activate"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                # AUTO-LOAD ON LOGIN
                saved_data = load_from_neon()
                if saved_data:
                    st.session_state.update(saved_data)
                st.rerun()
            else: st.error("Invalid Key")
        return False
    return True

# 4. PDF Generator (Logic Kept Intact)
def create_pdf(school_name, header, sub, df):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 22)
        pdf.cell(190, 15, str(school_name).upper(), ln=True, align='C')
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, str(header), ln=True, align='C')
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(190, 8, str(sub), ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 9)
        cols = ["Time Slot"] + list(df.columns)
        w = 190 / len(cols)
        for col in cols: pdf.cell(w, 10, str(col), 1, 0, 'C')
        pdf.ln()
        pdf.set_font("Arial", '', 8)
        for i in range(len(df)):
            pdf.cell(w, 10, str(df.index[i]), 1, 0, 'C')
            for col in df.columns:
                val = str(df[col][i]).encode('ascii', 'ignore').decode('ascii')
                pdf.cell(w, 10, val, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    except: return None

# 5. Main ERP Logic
if check_license():
    # Helper to get session state with defaults
    def get_val(key, default):
        return st.session_state.get(key, default)

    with st.sidebar:
        st.header(" School Setup")
        custom_school_name = st.text_input("Enter School Name:", get_val("school_name", "Global Excellence Academy"))
        st.divider()
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], get_val("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]))
        
        # Time handling for JSON compatibility
        start_val = datetime.strptime(get_val("start_t", "08:00"), "%H:%M")
        end_val = datetime.strptime(get_val("end_t", "14:00"), "%H:%M")
        
        start_t = st.time_input("Open", start_val)
        end_t = st.time_input("Close", end_val)
        p_mins = st.number_input("Period Duration", 10, 120, get_val("p_mins", 40))
        brk_after = st.number_input("Break After Period", 1, 10, get_val("brk_after", 4))
        brk_mins = st.number_input("Break Mins", 10, 60, get_val("brk_mins", 30))
        
        st.divider()
        if st.button("Save Configuration", use_container_width=True, type="primary"):
            # Package all data into a dictionary for JSON
            payload = {
                "school_name": custom_school_name,
                "days": days,
                "start_t": start_t.strftime("%H:%M"),
                "end_t": end_t.strftime("%H:%M"),
                "p_mins": p_mins,
                "brk_after": brk_after,
                "brk_mins": brk_mins,
                "p_c": p_c_df.to_dict('records'),
                "p_t": p_t_df.to_dict('records'),
                "s_c": s_c_df.to_dict('records'),
                "s_t": s_t_df.to_dict('records'),
                "c_c": c_c_df.to_dict('records'),
                "c_t": c_t_df.to_dict('records'),
            }
            save_to_neon(custom_school_name, payload)
            st.sidebar.success("Settings Saved to Neon Database!")
            
        if st.button("Logout", use_container_width=True):
            st.session_state['authenticated'] = False
            st.rerun()

    st.title(f" {custom_school_name}")
    
    # Registration Tabs (Loading previous DF states if available)
    tab1, tab2, tab3 = st.tabs(["Primary Registration", "Secondary Registration", "College Registration"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        p_c_df = col1.data_editor(pd.DataFrame(get_val("p_c", [{"Class": "Grade 1", "Sections": 1}])), num_rows="dynamic", key="editor_p_c")
        p_t_df = col2.data_editor(pd.DataFrame(get_val("p_t", [{"Name": "", "Subject": ""}] * 5)), num_rows="dynamic", key="editor_p_t")
    with tab2:
        col1, col2 = st.columns([1, 2])
        s_c_df = col1.data_editor(pd.DataFrame(get_val("s_c", [{"Class": "Grade 9", "Sections": 1}])), num_rows="dynamic", key="editor_s_c")
        s_t_df = col2.data_editor(pd.DataFrame(get_val("s_t", [{"Name": "", "Subject": ""}] * 5)), num_rows="dynamic", key="editor_s_t")
    with tab3:
        col1, col2 = st.columns([1, 2])
        c_c_df = col1.data_editor(pd.DataFrame(get_val("c_c", [{"Class": "FSc-1", "Sections": 1}])), num_rows="dynamic", key="editor_c_c")
        c_t_df = col2.data_editor(pd.DataFrame(get_val("c_t", [{"Name": "", "Subject": ""}] * 5)), num_rows="dynamic", key="editor_c_t")

    # --- Analysis Logic (Unchanged as per request) ---
    if st.button(" Run Analysis"):
        def process_list(c_df, t_df):
            cls = []
            for _, r in c_df.iterrows():
                if r["Class"]:
                    for i in range(int(r["Sections"])): cls.append(f"{r['Class']} (Sec {i+1})")
            tea = [f"{r['Name']} ({r['Subject']})" for _, r in t_df.iterrows() if r["Name"]]
            return cls, tea

        p_cls, p_tea = process_list(p_c_df, p_t_df)
        s_cls, s_tea = process_list(s_c_df, s_t_df)
        c_cls, c_tea = process_list(c_c_df, c_t_df)

        slots = []
        curr = datetime.combine(datetime.today(), start_t)
        limit = datetime.combine(datetime.today(), end_t)
        idx = 1
        while curr + timedelta(minutes=p_mins) <= limit:
            t_str = f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=p_mins)).strftime('%I:%M %p')}"
            slots.append({"time": t_str, "brk": False})
            curr += timedelta(minutes=p_mins)
            if idx == brk_after and curr + timedelta(minutes=brk_mins) <= limit:
                slots.append({"time": f"{curr.strftime('%I:%M %p')}-{(curr+timedelta(minutes=brk_mins)).strftime('%I:%M %p')}", "brk": True})
                curr += timedelta(minutes=brk_mins)
            idx += 1

        master = {}; class_schedules = {}; stats = {"Primary": {"T":0, "F":0}, "Secondary": {"T":0, "F":0}, "College": {"T":0, "F":0}}
        all_sections = [{"id": "Primary", "c": p_cls, "t": p_tea}, {"id": "Secondary", "c": s_cls, "t": s_tea}, {"id": "College", "c": c_cls, "t": c_tea}]

        for sec in all_sections:
            for cls in sec["c"]:
                day_plans = {}
                for d in days:
                    slot_list = []
                    for s in slots:
                        if s["brk"]: slot_list.append(" BREAK")
                        else:
                            stats[sec["id"]]["T"] += 1
                            avail = [t for t in sec["t"] if (d, s["time"], t) not in master and (d, cls, t) not in master]
                            if avail:
                                pk = random.choice(avail); master[(d, s["time"], pk)] = cls
                                master[(d, cls, pk)] = True; slot_list.append(pk); stats[sec["id"]]["F"] += 1
                            else: slot_list.append(" NO STAFF")
                    day_plans[d] = slot_list
                class_schedules[cls] = pd.DataFrame(day_plans, index=[s['time'] for s in slots])

        # Analysis UI (Profit Levels preserved)
        st.markdown("---")
        st.header(f" {custom_school_name}: Profit & Efficiency Analysis")
        m1, m2, m3 = st.columns(3)
        all_f = sum(x["F"] for x in stats.values()); all_t = sum(x["T"] for x in stats.values())
        eff = (all_f / all_t * 100) if all_t > 0 else 0
        m1.metric("Overall Efficiency", f"{eff:.1f}%")
        m2.metric("Total Active Sections", len(class_schedules))
        m3.metric("Profit Status", "Optimized" if eff > 85 else "Action Required")

        st.write("#### Section-Wise Performance")
        s_col1, s_col2, s_col3 = st.columns(3)
        for i, (name, s_data) in enumerate(stats.items()):
            col = [s_col1, s_col2, s_col3][i]
            with col:
                e_val = (s_data["F"]/s_data["T"]*100) if s_data["T"] > 0 else 0
                st.info(f"**{name.upper()}**\n\nEfficiency: {e_val:.1f}%\nVacancies: {s_data['T']-s_data['F']}")

        st.markdown("---")
        st.header(" Student Class Schedules")
        for cls_name, df in class_schedules.items():
            with st.expander(f"View: {cls_name}"):
                st.table(df)
                p = create_pdf(custom_school_name, "STUDENT TIMETABLE", f"Class: {cls_name}", df)
                st.download_button(f" Print {cls_name} PDF", p, f"{cls_name}.pdf", "application/pdf", key=f"b_{cls_name}")

        st.markdown("---")
        st.header(" Teacher Duty Charts")
        for t in (p_tea + s_tea + c_tea):
            t_duty = {d: [master.get((d, s["time"], t), "FREE") if not s["brk"] else "BREAK" for s in slots] for d in days}
            df_t = pd.DataFrame(t_duty, index=[s['time'] for s in slots])
            with st.expander(f"View: {t}"):
                st.table(df_t)
                tp = create_pdf(custom_school_name, "TEACHER DUTY CHART", f"Teacher: {t}", df_t)
                st.download_button(f" Print {t} PDF", tp, f"{t}.pdf", "application/pdf", key=f"tb_{t}")
