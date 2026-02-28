import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import datetime
from matplotlib.patches import Patch

# --- APP CONFIG & STATE ---
st.set_page_config(page_title="Bio-Clock Tracker Pro", page_icon="⌚", layout="wide")
st.title("24-Hour Multi-Activity Bio-Clock 🌙🏃🍴")

# Initialization for all trackers
for key in ['sleep_count', 'meal_count', 'activity_count']:
    if key not in st.session_state:
        st.session_state[key] = 1

def add_item(key): st.session_state[key] += 1
def remove_item(key):
    if st.session_state[key] > 1: st.session_state[key] -= 1

# --- SIDEBAR: LOGGING CONTROLS ---
with st.sidebar:
    st.header("🌙 Sleep Log (Innermost)")
    sleeps = []
    for i in range(st.session_state.sleep_count):
        col1, col2 = st.columns(2)
        s = col1.time_input(f"Bed {i+1}", value=datetime.time(23, 0), key=f"s_{i}", step=datetime.timedelta(minutes=5))
        e = col2.time_input(f"Wake {i+1}", value=datetime.time(7, 0), key=f"e_{i}", step=datetime.timedelta(minutes=5))
        sleeps.append((s, e))
    st.button("➕ Add Sleep", on_click=add_item, args=('sleep_count',), key="btn_as")

    st.divider()
    st.header("🏃 Activity Log (Middle)")
    activities = []
    for i in range(st.session_state.activity_count):
        act_type = st.selectbox(f"Type {i+1}", ["Walking", "Sitting", "Lying"], key=f"act_t_{i}")
        col1, col2 = st.columns(2)
        s = col1.time_input(f"Start {i+1}", value=datetime.time(10, 0), key=f"act_s_{i}", step=datetime.timedelta(minutes=5))
        e = col2.time_input(f"End {i+1}", value=datetime.time(11, 0), key=f"act_e_{i}", step=datetime.timedelta(minutes=5))
        activities.append({'type': act_type, 'start': s, 'end': e})
    st.button("➕ Add Activity", on_click=add_item, args=('activity_count',), key="btn_aa")

    st.divider()
    st.header("🍴 Meal Log (Outer)")
    meals = []
    for i in range(st.session_state.meal_count):
        m = st.time_input(f"Meal {i+1}", value=datetime.time(12, 0), key=f"m_{i}", step=datetime.timedelta(minutes=5))
        meals.append(m)
    st.button("➕ Add Meal", on_click=add_item, args=('meal_count',), key="btn_am")

# --- VISUALIZATION LOGIC ---
fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)

# Clock Styling
angles = np.linspace(0, 2 * np.pi, 24, endpoint=False)
ax.set_xticks(angles)
ax.set_xticklabels([f"{i}:00" for i in range(24)])
ax.set_yticks([]) 
ax.set_ylim(0, 1.1)

# Constants
num_segments = 288
segment_angle = 2 * np.pi / num_segments
ACT_COLORS = {"Walking": "#2ecc71", "Sitting": "#e67e22", "Lying": "#3498db"}

def is_time_in_range(t_mid, start, end):
    s_min = start.hour * 60 + start.minute
    e_min = end.hour * 60 + end.minute
    if s_min <= e_min: return s_min <= t_mid < e_min
    else: return t_mid >= s_min or t_mid < e_min 

# --- DRAWING LAYERS ---
for i in range(num_segments):
    t_mid = (i * 5) + 2.5 
    
    # 1. INNERMOST RING: Sleep (Radius 0.4 to 0.6)
    asleep = any(is_time_in_range(t_mid, s, e) for s, e in sleeps)
    ax.bar(i * segment_angle, 0.2, width=segment_angle, bottom=0.4, 
           color='black' if asleep else '#f8f9fa', edgecolor='white', linewidth=0.1, align='edge')

    # 2. MIDDLE RING: Activities (Radius 0.65 to 0.85)
    active_color = "#f8f9fa" 
    for act in activities:
        if is_time_in_range(t_mid, act['start'], act['end']):
            active_color = ACT_COLORS[act['type']]
            break
    ax.bar(i * segment_angle, 0.2, width=segment_angle, bottom=0.65, 
           color=active_color, edgecolor='white', linewidth=0.1, align='edge')

# 3. OUTERMOST RING: Meals (Radius 0.9 to 1.0)
for m in meals:
    meal_angle = (m.hour * 60 + m.minute) * (2 * np.pi / 1440)
    # Drawing a slightly wider wedge for visibility on the outer rim
    ax.bar(meal_angle, 0.1, width=0.08, bottom=0.9, color='#e74c3c')

# Legend
legend_elements = [
    Patch(facecolor='black', label='Sleep (Inner)'),
    Patch(facecolor='#2ecc71', label='Walking (Mid)'),
    Patch(facecolor='#e67e22', label='Sitting (Mid)'),
    Patch(facecolor='#3498db', label='Lying (Mid)'),
    Patch(facecolor='#e74c3c', label='Meal (Outer)')
]
ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.2, 1.1))

st.pyplot(fig)

# --- TOTALS SUMMARY ---
st.info("📊 **Visual Hierarchy:** Center → Sleep | Middle → Activity | Boundary → Meals")
