import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from fpdf import FPDF

# 1. Page Configuration
st.set_page_config(page_title="GEA Timetable ERP", layout="wide")

# 2. Advanced Security & Software Lock (Profit Level 200)
MASTER_KEY = "AhsanPro200"
EXPIRY_DATE = "2026-12-31" 

def check_license():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    # Check Expiry First
    current_date = datetime.now().date()
    expiry = datetime.strptime(EXPIRY_DATE, "%Y-%m-%d").date()
    
    if current_date > expiry:
        st.error("❌ SYSTEM LOCKED: LICENSE EXPIRED! Please contact the developer for a new update.")
        st.info(f"System Expiry was set to: {EXPIRY_DATE}")
        return False

    if not st.session_state['authenticated']:
        st.title("🔐 Enterprise Software Activation")
        st.warning("Global Excellence Academy - Professional Management System")
        user_key = st.text_input("Please enter your Master License Key:", type="password")
        if st.button("Activate System"):
            if user_key == MASTER_KEY:
                st.session_state['authenticated'] = True
                st.success("Verification Successful! Access Granted.")
                st.rerun()
            else:
                st.error("Invalid License Key. Please try again.")
        return False
    return True

# 3. Enhanced PDF Function (UTF-8 Compatible)
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
                # Clean text for PDF compatibility
                clean_text = str(df[col][i]).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(w, 10, clean_text, 1, 0, 'C')
            pdf.ln()
        return pdf.output(dest='S').encode('latin-1')
    except Exception:
        return None

# 4. Main Application
if check_license():
    st.title("🏫 Global Excellence Academy")
    st.subheader("Professional ERP Module: Intelligent Scheduling")

    with st.sidebar:
        st.header("⚙️ Timing Configuration")
        days = st.multiselect("Select Working Days", 
                             ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], 
                             ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        st.divider()
        school_start = st.time_input("School Opening Time", datetime.strptime("08:00", "%H:%M"))
        school_end = st.time_input("School Closing Time", datetime.strptime("14:00", "%H:%M"))
        period_duration = st.number_input("One Period (Mins)", 10, 120, 40)
        
        st.divider()
        after_period = st.number_input("Lunch Break After Period", 1, 10, 4)
        break_duration = st.number_input("Break Length (Mins)", 10, 60, 30)

    # Data Entry Section
    st.markdown("### 🏛️ Faculty & Section Management")
    tab1, tab2, tab3 = st.tabs(["👶 Primary Section", "🏫 Secondary Section", "🎓 College Section"])

    def manage_section_data(key_id, default_cls):
        c1, c2 = st.columns([1, 2])
        cls_input = c1.text_area(f"Enter Classes (Comma Separated)", default_cls, key=f"c_{key_id}")
        cls_list = [c.strip() for c in cls_input.split(",") if c.strip()]
        
        st.write(f"Assign Teachers and Subjects for {key_id.capitalize()}:")
        init_df = pd.DataFrame([{"Teacher Name": "", "Subject": ""}] * 5)
        edited_df = c2.data_editor(init_df, num_rows="dynamic", key=f"t_{key_id}")
        
        teachers_with_subs = []
        for _, row in edited_df.iterrows():
            if row["Teacher Name"]:
                teachers_with_subs.append(f"{row['Teacher Name']} ({row['Subject']})")
        return cls_list, teachers_with_subs

    with tab1: pri_cls, pri_tea = manage_section_data("primary", "Grade 1, Grade 2")
    with tab2: sec_cls, sec_tea = manage_section_data("secondary", "Grade 9, Grade 10")
    with tab3: coll_cls, coll_tea = manage_section_data("college", "FSc, BS-CS")

    if st.button("🚀 Generate All Reports"):
        # 1. Time Slot Logic
        time_slots = []
        current_time = datetime.combine(datetime.today(), school_start)
        closing_time = datetime.combine(datetime.today(), school_end)
        p_num = 1
        
        while current_time + timedelta(minutes=period_duration) <= closing_time:
            slot_range = f"{current_time.strftime('%I:%M %p')}-{(current_time + timedelta(minutes=period_duration)).strftime('%I:%M %p')}"
            time_slots.append({"label": f"P{p_num}", "time": slot_range, "is_break": False})
            current_time += timedelta(minutes=period_duration)
            
            if p_num == after_period and current_time + timedelta(minutes=break_duration) <= closing_time:
                break_range = f"{current_time.strftime('%I:%M %p')}-{(current_time + timedelta(minutes=break_duration)).strftime('%I:%M %p')}"
                time_slots.append({"label": "BREAK", "time": break_range, "is_break": True})
                current_time += timedelta(minutes=break_duration)
            p_num += 1

        if not time_slots:
            st.error("The selected school timing is too short for any periods.")
        else:
            master_registry = {} # Tracking: (day, time, teacher) -> class
            taught_today = {} # Tracking: (day, class) -> [list of teachers]
            
            sections = [
                {"name": "Primary", "classes": pri_cls, "teachers": pri_tea},
                {"name": "Secondary", "classes": sec_cls, "teachers": sec_tea},
                {"name": "College", "classes": coll_cls, "teachers": coll_tea}
            ]

            # --- PART 1: CLASS TIMETABLES ---
            st.header("📋 SECTION 1: STUDENT CLASS TIMETABLES")
            for sec in sections:
                if not sec["classes"]: continue
                for cls in sec["classes"]:
                    cls_plan = {}
                    for day in days:
                        day_list = []
                        for slot in time_slots:
                            if slot["is_break"]:
                                day_list.append("☕ BREAK")
                            else:
                                if (day, cls) not in taught_today: taught_today[(day, cls)] = []
                                
                                # NO-REPEAT LOGIC: Free and hasn't taught this class today
                                avail = [t for t in sec["teachers"] if 
                                         (day, slot["time"], t) not in master_registry and 
                                         t not in taught_today[(day, cls)]]
                                
                                if avail:
                                    choice = random.choice(avail)
                                    master_registry[(day, slot["time"], choice)] = cls
                                    taught_today[(day, cls)].append(choice)
                                    day_list.append(choice)
                                else:
                                    day_list.append("❌ NO STAFF")
                        cls_plan[day] = day_list
                    
                    df_cls = pd.DataFrame(cls_plan, index=[s['time'] for s in time_slots])
                    st.write(f"**Timetable: {cls}**")
                    st.table(df_cls)
                    pdf_c = create_pdf("Global Excellence Academy", f"Class Schedule: {cls}", df_cls)
                    if pdf_c: st.download_button(f"📥 Download {cls} PDF", pdf_c, f"{cls}.pdf", key=f"d_{cls}")

            # --- PART 2: TEACHER DUTY CHARTS ---
            st.divider()
            st.header("👨‍🏫 SECTION 2: FACULTY DUTY CHARTS")
            all_teachers = pri_tea + sec_tea + coll_tea
            for t in all_teachers:
                t_plan = {}
                for day in days:
                    t_day_list = []
                    for slot in time_slots:
                        if slot["is_break"]:
                            t_day_list.append("RECESSS")
                        else:
                            t_day_list.append(master_registry.get((day, slot["time"], t), "FREE"))
                    t_plan[day] = t_day_list
                
                df_t = pd.DataFrame(t_plan, index=[s['time'] for s in time_slots])
                with st.expander(f"Duty Chart: {t}"):
                    st.table(df_t)
                    pdf_t = create_pdf("Global Excellence Academy", f"Faculty Duty Chart: {t}", df_t)
                    if pdf_t: st.download_button(f"📥 Download {t} PDF", pdf_t, f"Teacher_{t}.pdf", key=f"dt_{t}")

