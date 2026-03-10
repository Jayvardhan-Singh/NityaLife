import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import datetime
import pandas as pd
import io
from matplotlib.patches import Patch

# ==========================================
# CHUNK 1: APP CONFIGURATION & STATE RESET
# PROBLEM SOLVED: Sets up the page layout. Added `initial_sidebar_state="expanded"`
# so the user immediately sees the input controls without having to click to open them.
# ==========================================
st.set_page_config(
    page_title="NityaBioClock", 
    page_icon="⌚", 
    layout="wide", 
    initial_sidebar_state="expanded"
)
st.title("Nitya Bio-Clock 🌙🚶‍♂️🍴")

st.info("""
**📋 Instructions for Use:**
1. Log your timings for an **Average Weekday**.
2. Mark your **Sleep**, **Brisk Walk+** (activity), and **Meals**.
3. **Important:** A "Meal" comprises *anything* consumed other than plain water (e.g., snacks, coffee with milk, juices all count).
4. In Activity Mark time of Brisk walk and all activities more severe to Brisk Walk.
""")

# Callback function to completely reset the app state
def reset_app():
    st.session_state.clear()

# Initialize row counters
for key in ['sleep_count', 'meal_count', 'activity_count']:
    if key not in st.session_state:
        st.session_state[key] = 1

def add_item(key): st.session_state[key] += 1
def remove_item(key):
    if st.session_state[key] > 1: st.session_state[key] -= 1

# ==========================================
# CHUNK 2: USER METADATA & DATA MANAGEMENT
# PROBLEM SOLVED: Collects user details to stamp on the final chart and provides
# a global reset button to easily clear all fields for a new entry.
# ==========================================
with st.sidebar:
    st.header("👤 Personal Details")
    user_name = st.text_input("Name", value="User", key="user_name_input")
    user_age = st.number_input("Age", min_value=0, max_value=120, value=25, key="user_age_input")
    
    selected_date = st.date_input("Date (Local Time)", value=datetime.date.today(), key="date_input")
    formatted_date = selected_date.strftime("%B %d, %Y")
    
    st.divider()
    st.button("🔄 Reset All Data", on_click=reset_app, use_container_width=True)
    st.divider()

sleeps, activities, meals = [], [], []

# ==========================================
# CHUNK 3: MANUAL DATA INGESTION
# PROBLEM SOLVED: Renders the dynamic input fields in the sidebar based on the 
# session state counters, allowing users to log multiple events of each type.
# ==========================================
with st.sidebar:
    st.subheader("🌙 Sleep")
    for i in range(st.session_state.sleep_count):
        col1, col2 = st.columns(2)
        s = col1.time_input(f"Bed {i+1}", value=datetime.time(23, 0), key=f"s_{i}", step=datetime.timedelta(minutes=5))
        e = col2.time_input(f"Wake {i+1}", value=datetime.time(7, 0), key=f"e_{i}", step=datetime.timedelta(minutes=5))
        sleeps.append((s, e))
    st.button("➕ Add Sleep", on_click=add_item, args=('sleep_count',))
    
    st.subheader("🚶‍♂️ Brisk Walk+")
    for i in range(st.session_state.activity_count):
        col1, col2 = st.columns(2)
        s = col1.time_input(f"Start {i+1}", value=datetime.time(8, 0), key=f"act_s_{i}", step=datetime.timedelta(minutes=5))
        e = col2.time_input(f"End {i+1}", value=datetime.time(9, 0), key=f"act_e_{i}", step=datetime.timedelta(minutes=5))
        activities.append({'start': s, 'end': e})
    st.button("➕ Add Walk", on_click=add_item, args=('activity_count',))

    st.subheader("🍴 Meals")
    for i in range(st.session_state.meal_count):
        m = st.time_input(f"Meal {i+1}", value=datetime.time(13, 0), key=f"m_{i}", step=datetime.timedelta(minutes=5))
        meals.append(m)
    st.button("➕ Add Meal", on_click=add_item, args=('meal_count',))

# ==========================================
# CHUNK 4: METRIC CALCULATIONS
# PROBLEM SOLVED: Calculates total duration for sleep/walk and finds the maximum
# interval between consecutive meals (including the overnight gap).
# ==========================================
def calc_duration(s, e):
    sm, em = s.hour*60+s.minute, e.hour*60+e.minute
    return (em - sm) if em >= sm else (1440 - sm + em)

total_sleep_mins = sum(calc_duration(s, e) for s, e in sleeps)
sleep_str = f"{total_sleep_mins // 60}h {total_sleep_mins % 60}m"

total_walk_mins = sum(calc_duration(a['start'], a['end']) for a in activities)
walk_str = f"{total_walk_mins // 60}h {total_walk_mins % 60}m"

max_fast_mins = 0
if len(meals) > 1:
    meal_mins = sorted([m.hour * 60 + m.minute for m in meals])
    fasts = [meal_mins[i+1] - meal_mins[i] for i in range(len(meal_mins)-1)]
    fasts.append((meal_mins[0] + 1440) - meal_mins[-1])
    max_fast_mins = max(fasts)
elif len(meals) == 1:
    max_fast_mins = 1440
fast_str = f"{max_fast_mins // 60}h {max_fast_mins % 60}m"

# ==========================================
# CHUNK 5: MATPLOTLIB CHART
# PROBLEM SOLVED: Configures the 24-hour polar projection and stamps the 
# calculated metrics and user metadata directly onto the figure canvas.
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
fig.text(0.05, 0.89, f"Date: {formatted_date}", fontsize=10)

# Health Metrics (Top Right)
fig.text(0.68, 0.95, f"Total 'Night' Sleep: {sleep_str}", fontsize=10, fontweight='bold')
fig.text(0.68, 0.92, f"Total Brisk+: {walk_str}", fontsize=10, fontweight='bold', color='#27ae60')
fig.text(0.68, 0.89, f"Max Fasting: {fast_str}", fontsize=10, fontweight='bold', color='#c0392b')

# ==========================================
# CHUNK 6: UNIFIED SINGLE-RING DRAWING
# PROBLEM SOLVED: Evaluates every 5-minute block of the day and colors it based 
# on a hierarchy (Meal > Walk > Sleep) to create a single clean visual ring.
# ==========================================
num_segments = 288
segment_angle = 2 * np.pi / num_segments

def is_in(t, s, e):
    sm, em = s.hour*60+s.minute, e.hour*60+e.minute
    return sm <= t < em if sm <= em else t >= sm or t < em

for i in range(num_segments):
    t_mid = (i * 5) + 2.5 
    
    slp = any(is_in(t_mid, s, e) for s, e in sleeps)
    wlk = any(is_in(t_mid, a['start'], a['end']) for a in activities)
    ml = any(m.hour*60+m.minute >= i*5 and m.hour*60+m.minute < (i+1)*5 for m in meals)
    
    color = '#f8f9fa' # Default awake/inactive background
    if ml:
        color = '#e74c3c' # Red (Meal)
    elif wlk:
        color = '#2ecc71' # Green (Walk)
    elif slp:
        color = 'black'   # Black (Sleep)

    ax.bar(i*segment_angle, 0.4, width=segment_angle, bottom=0.5, 
           color=color, edgecolor='white', linewidth=0.1, align='edge')

# Updated Legend
legend_elements = [Patch(facecolor='black', label='Sleep'), Patch(facecolor='#2ecc71', label='Brisk Walk+'), Patch(facecolor='#e74c3c', label='Meal')]
ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.1), ncol=3)

# ==========================================
# CHUNK 7: RENDERING & EXPORT
# PROBLEM SOLVED: Renders the plot in the UI and creates downloadable files 
# (PNG for the visual, CSV for the raw data) directly from memory.
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
        st.download_button("📄 Download Data (CSV)", pd.DataFrame(csv_rows).to_csv(index=False), f"{user_name}_data.csv", "text/csv")
