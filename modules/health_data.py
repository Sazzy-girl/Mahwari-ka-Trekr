import streamlit as st
import pandas as pd
import base64

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

def render_water_tracker(t=None):
    if t is None: t = {"water_tracker": "💧 Water Intake Tracker", "glasses": "Glasses", "add": "➕ Add", "reset": "🔄 Reset"}
    st.markdown(f"### {t.get('water_tracker', '💧 Water Intake Tracker')}")
    
    if "water_count" not in st.session_state:
        st.session_state["water_count"] = 0
        
    goal = 8
    progress = min(st.session_state["water_count"] / goal, 1.0)
    
    # Custom Glass Progress Bar
    st.markdown(f"""
    <div style="background-color: rgba(255,255,255,0.1); border-radius: 10px; padding: 3px; margin-bottom: 20px;">
        <div style="width: {progress*100}%; background: linear-gradient(90deg, #00c6ff, #0072ff); height: 20px; border-radius: 8px; transition: width 0.5s;"></div>
    </div>
    <div style="text-align: center; margin-bottom: 20px; color: #00c6ff; font-weight: bold; font-size: 1.2em;">
        {st.session_state["water_count"]} / {goal} {t.get('glasses', 'Glasses')}
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t.get('add', '➕ Add'), use_container_width=True):
            st.session_state["water_count"] += 1
            st.rerun()
    with col2:
        if st.button(t.get('reset', '🔄 Reset'), use_container_width=True):
            st.session_state["water_count"] = 0
            st.rerun()

def render_exercise_guide(t=None):
    if t is None: t = {"exercise_guide": "Exercise Guide", "note": "Note", "consistency_msg": "Consistency is key. 5 days a week."}
    st.markdown(f"<h2 style='color: var(--primary-color);'>{t.get('exercise_guide', 'Exercise Guide')}</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='glass-card' style='padding: 10px; margin-bottom: 20px;'><strong>{t.get('note', 'Note')}:</strong> {t.get('consistency_msg', 'Consistency is key.')}</div>", unsafe_allow_html=True)
    
    # Data from sample project
    sections = [
        {
            "title": "1. Cardio Exercises",
            "desc": "Increases heart rate and burns fat.",
            "items": [
                { "name": "Brisk Walking", "note": "30-45 mins daily improves insulin sensitivity.", "img": "assets/walking.png" },
                { "name": "Cycling", "note": "Strengthens abs and reduces weight.", "img": "assets/cycling.png" },
                { "name": "Swimming", "note": "Great for hormone balance.", "img": "assets/swimming.png" }
            ]
        },
        {
            "title": "2. Yoga Asanas",
            "desc": "Reduces stress and balances hormones.",
            "items": [
                { "name": "Butterfly Pose", "note": "Increases blood flow to ovaries.", "img": "assets/butterfly.png" },
                { "name": "Cobra Pose", "note": "Stretches abdomen, fixes period issues.", "img": "assets/cobra.png" },
                { "name": "Bow Pose", "note": "Stimulates reproductive organs.", "img": "assets/bow.png" },
                { "name": "Surya Namaskar", "note": "Revitalizes entire body. 10-12 sets.", "img": "assets/surya.png" }
            ]
        },
        {
            "title": "3. Strength Training",
            "desc": "Muscle building regulates blood sugar.",
            "items": [
                { "name": "Squats", "note": "Strengthens legs and hips.", "img": "assets/squat.png" },
                { "name": "Plank", "note": "Strengthens core muscles.", "img": "assets/plank.png" },
                { "name": "Light Weights", "note": "2-3 times a week.", "img": "assets/weights.png" }
            ]
        }
    ]
    
    for section in sections:
        st.markdown(f"### {section['title']}")
        st.caption(section['desc'])
        
        for item in section['items']:
            b64_img = get_base64_image(item['img'])
            img_tag = f'<img src="data:image/png;base64,{b64_img}" class="exercise-img">' if b64_img else ''
            
            st.markdown(f"""
            <div class="exercise-card">
                {img_tag}
                <div class="exercise-info">
                    <h4>{item['name']}</h4>
                    <p>{item['note']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
