import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Sleep Tracker Visualizer", page_icon="🌙", layout="wide")

# --- HELPER FUNCTION ---
def time_to_datetime(target_time, base_time, base_date):
    """
    Intelligently converts a time object to a datetime object, handling the midnight rollover.
    If the target_time is an AM hour and the base_time (bed time) is a PM hour, 
    we assume the target_time happens on the next day.
    """
    dt = datetime.combine(base_date, target_time)
    # If bed time was PM and this time is AM, it's likely the next day
    if base_time.hour >= 12 and target_time.hour < 12:
        dt += timedelta(days=1)
    # If bed time was early AM and the event was the previous PM (e.g. last meal at 8 PM, bed at 1 AM)
    elif base_time.hour < 12 and target_time.hour >= 12:
        dt -= timedelta(days=1)
    return dt

# --- UI LOGIC ---
st.title("🌙 Sleep Timeline Visualizer")
st.markdown("Enter your sleep metrics below to generate a layered timeline of your night.")

st.sidebar.header("Log Your Night")

# 1. Time in Bed Inputs
st.sidebar.subheader("Time in Bed")
bed_start = st.sidebar.time_input("Got into bed at", value=datetime.strptime("22:00", "%H:%M").time())
bed_end = st.sidebar.time_input("Got out of bed at", value=datetime.strptime("07:00", "%H:%M").time())

# 2. Actual Sleep Inputs
st.sidebar.subheader("Actual Sleep")
sleep_start = st.sidebar.time_input("Fell asleep at", value=datetime.strptime("23:00", "%H:%M").time())
sleep_end = st.sidebar.time_input("Woke up at", value=datetime.strptime("06:30", "%H:%M").time())

# 3 & 4. Event Inputs (Refined for Pre-Sleep Hygiene)
st.sidebar.subheader("Hygiene Events")
last_meal = st.sidebar.time_input("Last meal before bed", value=datetime.strptime("19:30", "%H:%M").time())
screen_time = st.sidebar.time_input("Last screen time", value=datetime.strptime("22:45", "%H:%M").time())

# --- DATA PROCESSING ---
base_date = date.today()

# Convert all times to datetimes relative to the 'bed_start' to handle midnight rollovers
dt_bed_start = datetime.combine(base_date, bed_start)
dt_bed_end = time_to_datetime(bed_end, bed_start, base_date)

dt_sleep_start = time_to_datetime(sleep_start, bed_start, base_date)
dt_sleep_end = time_to_datetime(sleep_end, bed_start, base_date)

dt_last_meal = time_to_datetime(last_meal, bed_start, base_date)
dt_screen_time = time_to_datetime(screen_time, bed_start, base_date)

# --- VISUALIZATION ---
fig = go.Figure()

# Base Layer: Time in Bed
fig.add_trace(go.Scatter(
    x=[dt_bed_start, dt_bed_end],
    y=["Sleep Timeline", "Sleep Timeline"],
    mode="lines",
    line=dict(color="#B0C4DE", width=50), # Light Steel Blue
    name="Time in Bed",
    hoverinfo="x+name"
))

# Top Layer: Actual Time Slept
fig.add_trace(go.Scatter(
    x=[dt_sleep_start, dt_sleep_end],
    y=["Sleep Timeline", "Sleep Timeline"],
    mode="lines",
    line=dict(color="#4169E1", width=30), # Royal Blue
    name="Actual Sleep",
    hoverinfo="x+name"
))

# Vertical Line: Last Meal
fig.add_vline(
    x=dt_last_meal.timestamp() * 1000, 
    line_dash="dot", line_color="orange", annotation_text="Last Meal", 
    annotation_position="top left", annotation_font_color="orange"
)

# Vertical Line: Last Screen Time
fig.add_vline(
    x=dt_screen_time.timestamp() * 1000, 
    line_dash="dash", line_color="red", annotation_text="Last Screen Time", 
    annotation_position="bottom right", annotation_font_color="red"
)

# Layout Formatting
fig.update_layout(
    title="Nightly Sleep Pattern Analysis",
    xaxis_title="Time",
    yaxis_title="",
    height=400,
    showlegend=True,
    xaxis=dict(
        tickformat="%I:%M %p", 
        gridcolor='rgba(0,0,0,0.1)'
    ),
    plot_bgcolor="white"
)

# Render in Streamlit
st.plotly_chart(fig, use_container_width=True)

# Add a summary metric section below
st.markdown("---")
col1, col2 = st.columns(2)
time_in_bed_hrs = (dt_bed_end - dt_bed_start).total_seconds() / 3600
actual_sleep_hrs = (dt_sleep_end - dt_sleep_start).total_seconds() / 3600

with col1:
    st.metric("Total Time in Bed", f"{time_in_bed_hrs:.1f} hrs")
with col2:
    st.metric("Actual Time Slept", f"{actual_sleep_hrs:.1f} hrs")
