import streamlit as st
import pandas as pd

def render_water_tracker():
    st.markdown("### 💧 Water Intake Tracker")
    
    if "water_count" not in st.session_state:
        st.session_state["water_count"] = 0
        
    goal = 8
    progress = min(st.session_state["water_count"] / goal, 1.0)
    
    # Custom Glass Progress Bar
    st.markdown(f"""
    <div style="background-color: rgba(255,255,255,0.1); border-radius: 10px; padding: 3px;">
        <div style="width: {progress*100}%; background: linear-gradient(90deg, #00c6ff, #0072ff); height: 20px; border-radius: 8px; transition: width 0.5s;"></div>
    </div>
    <div style="text-align: center; margin-top: 10px; color: #00c6ff; font-weight: bold;">
        {st.session_state["water_count"]} / {goal} Glasses
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Glass"):
            st.session_state["water_count"] += 1
            st.rerun()
    with col2:
        if st.button("🔄 Reset"):
            st.session_state["water_count"] = 0
            st.rerun()

def render_exercise_guide():
    st.markdown("### 🧘‍♀️ Hormonal Health Exercises")
    
    exercises = [
        {"title": "Cobra Pose (Bhujangasana)", "desc": "Stretches abdominal muscles and improves circulation.", "type": "Yoga"},
        {"title": "Butterfly Pose (Baddha Konasana)", "desc": "Stimulates ovaries and improves reproductive health.", "type": "Yoga"},
        {"title": "Brisk Walking", "desc": "30 mins daily helps regulate insulin and hormones.", "type": "Cardio"},
        {"title": "Strength Training", "desc": "Building muscle mass helps metabolism.", "type": "Workout"}
    ]
    
    for ex in exercises:
        st.markdown(f"""
        <div class="glass-card">
            <h4>{ex['title']} <span style="font-size: 0.8em; background: #ff69b4; padding: 2px 8px; border-radius: 10px; color: white;">{ex['type']}</span></h4>
            <p>{ex['desc']}</p>
        </div>
        """, unsafe_allow_html=True)
