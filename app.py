import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import datetime
import pandas as pd
import io
from matplotlib.patches import Patch

# ==========================================
# CHUNK 1: APP CONFIGURATION & INSTRUCTIONS
# PROBLEM SOLVED: Users need clear definitions of what to track (Average Weekday, what counts as a meal).
# We use st.info() to create a highly visible instruction box right at the top.
# ==========================================
st.set_page_config(page_title="Nitya Bio-Clock", page_icon="⌚", layout="wide")
st.title("Nitya Bio-Clock")

st.info("""
**📋 Instructions for Use:**
1. Log your timings for an **Average Weekday**.
2. Mark your **Sleep**, **Brisk Walk+** (activity), and **Meals**.
3. **Important:** A "Meal" comprises *anything* consumed other than plain water (e.g., snacks, coffee with milk, juices all count).
4. In Activity Mark time of Brisk walk and all activities more severe to Brisk Walk.
5. If you want to upload a csv file, kindly download a sample of csv file first and upload a csv with the same headers and categories.
""")

# Initialize counters
for key in ['sleep_count', 'meal_count', 'activity_count']:
    if key not in st.session_state:
        st.session_state[key] = 1

def add_item(key): st.session_state[key] += 1
def remove_item(key):
    if st.session_state[key] > 1: st.session_state[key] -= 1

# ==========================================
# CHUNK 2: USER METADATA INPUT
# ==========================================
with st.sidebar:
    st.header("👤 Personal Details")
    user_name = st.text_input("Name", value="User")
    user_age = st.number_input("Age", min_value=0, max_value=120, value=25)

    # current_date = datetime.date.today().strftime("%B %d, %Y")
    # Using date_input solves the timezone discrepancy by letting the user confirm the date.
    selected_date = st.date_input("Date (Local Time)", value=datetime.date.today())
    current_date = selected_date.strftime("%B %d, %Y")

    st.divider()
    st.header("📂 Data Management")
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])

sleeps, activities, meals = [], [], []

# ==========================================
# CHUNK 3: DATA INGESTION
# ==========================================
if uploaded_file is not None:
    try:
        df_uploaded = pd.read_csv(uploaded_file)
        if {'Category', 'Start_Time', 'End_Time'}.issubset(df_uploaded.columns):
            for index, row in df_uploaded.iterrows():
                try:
                    start_t = pd.to_datetime(row['Start_Time']).time()
                    if row['Category'] == 'Meal':
                        meals.append(start_t)
                    else:
                        end_t = pd.to_datetime(row['End_Time']).time()
                        if row['Category'] == 'Sleep': 
                            sleeps.append((start_t, end_t))
                        elif row['Category'] == 'Brisk Walk+': 
                            activities.append({'start': start_t, 'end': end_t})
                except Exception: 
                    continue 
            st.sidebar.success("CSV Successfully Loaded! Clear file to input manually.")
        else:
            st.sidebar.error("Invalid CSV Format. Missing required columns.")
    except Exception: 
        st.sidebar.error("Error reading the file.")
else:
    with st.sidebar:
        st.subheader("🌙 Sleep (Innermost)")
        for i in range(st.session_state.sleep_count):
            col1, col2 = st.columns(2)
            s = col1.time_input(f"Bed {i+1}", value=datetime.time(23, 0), key=f"s_{i}", step=datetime.timedelta(minutes=5))
            e = col2.time_input(f"Wake {i+1}", value=datetime.time(7, 0), key=f"e_{i}", step=datetime.timedelta(minutes=5))
            sleeps.append((s, e))
        st.button("➕ Add Sleep", on_click=add_item, args=('sleep_count',))
        
        st.subheader("🚶‍♂️ Brisk Walk+ (Middle)")
        for i in range(st.session_state.activity_count):
            col1, col2 = st.columns(2)
            s = col1.time_input(f"Start {i+1}", value=datetime.time(8, 0), key=f"act_s_{i}", step=datetime.timedelta(minutes=5))
            e = col2.time_input(f"End {i+1}", value=datetime.time(9, 0), key=f"act_e_{i}", step=datetime.timedelta(minutes=5))
            activities.append({'start': s, 'end': e})
        st.button("➕ Add Walk", on_click=add_item, args=('activity_count',))

        st.subheader("🍴 Meals (Outermost)")
        for i in range(st.session_state.meal_count):
            m = st.time_input(f"Meal {i+1}", value=datetime.time(13, 0), key=f"m_{i}", step=datetime.timedelta(minutes=5))
            meals.append(m)
        st.button("➕ Add Meal", on_click=add_item, args=('meal_count',))

# ==========================================
# CHUNK 4: METRIC CALCULATIONS (SLEEP, WALK, FASTING)
# PROBLEM SOLVED: Need to calculate total durations and max intervals, accounting
# for midnight wrap-arounds (e.g., fasting from 20:00 to 08:00 next day).
# ==========================================
def calc_duration(s, e):
    sm, em = s.hour*60+s.minute, e.hour*60+e.minute
    return (em - sm) if em >= sm else (1440 - sm + em)

# 1. Total Sleep
total_sleep_mins = sum(calc_duration(s, e) for s, e in sleeps)
sleep_str = f"{total_sleep_mins // 60}h {total_sleep_mins % 60}m"

# 2. Total Brisk+
total_walk_mins = sum(calc_duration(a['start'], a['end']) for a in activities)
walk_str = f"{total_walk_mins // 60}h {total_walk_mins % 60}m"

# 3. Max Fasting Interval
max_fast_mins = 0
if len(meals) > 1:
    # Sort meals chronologically by minutes past midnight
    meal_mins = sorted([m.hour * 60 + m.minute for m in meals])
    # Calculate gaps between consecutive meals during the day
    fasts = [meal_mins[i+1] - meal_mins[i] for i in range(len(meal_mins)-1)]
    # Calculate the overnight gap (from the last meal of the day to the first meal next day)
    fasts.append((meal_mins[0] + 1440) - meal_mins[-1])
    max_fast_mins = max(fasts)
elif len(meals) == 1:
    max_fast_mins = 1440 # 24 hours if only one meal

fast_str = f"{max_fast_mins // 60}h {max_fast_mins % 60}m"

# ==========================================
# CHUNK 5: MATPLOTLIB CHART & STAMPING
# PROBLEM SOLVED: We now place the Personal Details on the Top-Left 
# and the newly calculated Health Metrics on the Top-Right of the chart.
# ==========================================
fig, ax = plt.subplots(figsize=(10, 11), subplot_kw={'projection': 'polar'})
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
angles = np.linspace(0, 2 * np.pi, 24, endpoint=False)
ax.set_xticks(angles)
ax.set_xticklabels([f"{i}:00" for i in range(24)])
ax.set_yticks([]) 
ax.set_ylim(0, 1.1) 

# Personal Info (Top Left)
fig.text(0.05, 0.95, f"Name: {user_name}", fontsize=12, fontweight='bold')
fig.text(0.05, 0.92, f"Age: {user_age}", fontsize=10)
fig.text(0.05, 0.89, f"Date: {current_date}", fontsize=10)

# Health Metrics (Top Right)
fig.text(0.70, 0.95, f"Total Sleep: {sleep_str}", fontsize=11, fontweight='bold', color='black')
fig.text(0.70, 0.92, f"Total Brisk+: {walk_str}", fontsize=11, fontweight='bold', color='#27ae60')
fig.text(0.70, 0.89, f"Max Fasting: {fast_str}", fontsize=11, fontweight='bold', color='#c0392b')

# ==========================================
# CHUNK 6: DRAWING THE LAYERS
# ==========================================
num_segments = 288
segment_angle = 2 * np.pi / num_segments

def is_in(t, s, e):
    sm, em = s.hour*60+s.minute, e.hour*60+e.minute
    return sm <= t < em if sm <= em else t >= sm or t < em

for i in range(num_segments):
    t_mid = (i * 5) + 2.5 
    
    slp = any(is_in(t_mid, s, e) for s, e in sleeps)
    ax.bar(i*segment_angle, 0.2, width=segment_angle, bottom=0.4, color='black' if slp else '#f8f9fa', edgecolor='white', linewidth=0.1, align='edge')
    
    wlk = any(is_in(t_mid, a['start'], a['end']) for a in activities)
    ax.bar(i*segment_angle, 0.2, width=segment_angle, bottom=0.65, color='#2ecc71' if wlk else '#f8f9fa', edgecolor='white', linewidth=0.1, align='edge')
    
    ml = any(m.hour*60+m.minute >= i*5 and m.hour*60+m.minute < (i+1)*5 for m in meals)
    ax.bar(i*segment_angle, 0.2, width=segment_angle, bottom=0.9, color='#e74c3c' if ml else '#f8f9fa', edgecolor='white', linewidth=0.1, align='edge')

legend_elements = [Patch(facecolor='black', label='Sleep'), Patch(facecolor='#2ecc71', label='Brisk Walk+'), Patch(facecolor='#e74c3c', label='Meal')]
ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=3)

# ==========================================
# CHUNK 7: RENDERING & EXPORT
# ==========================================
col_left, col_right = st.columns([3, 1])
with col_left:
    st.pyplot(fig)

with col_right:
    st.subheader("💾 Export")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    st.download_button("🖼️ Download Chart (PNG)", buf.getvalue(), f"{user_name}_bioclock.png", "image/png")
    
    csv_rows = []
    for s, e in sleeps: csv_rows.append({"Category": "Sleep", "Start_Time": s.strftime("%H:%M"), "End_Time": e.strftime("%H:%M")})
    for a in activities: csv_rows.append({"Category": "Brisk Walk+", "Start_Time": a['start'].strftime("%H:%M"), "End_Time": a['end'].strftime("%H:%M")})
    for m in meals: csv_rows.append({"Category": "Meal", "Start_Time": m.strftime("%H:%M"), "End_Time": m.strftime("%H:%M")})
    
    if csv_rows:
        df_export = pd.DataFrame(csv_rows)
        st.download_button("📄 Download Data (CSV)", df_export.to_csv(index=False), f"{user_name}_data.csv", "text/csv")
