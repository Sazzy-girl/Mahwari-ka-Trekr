import streamlit as st
import pandas as pd
from datetime import datetime, date
import time

# Module Imports
from modules.database_setup import init_db
from modules.auth import (
    render_auth, 
    get_user_settings, 
    update_user_setting, 
    change_pin 
)
from modules.calendar_logic import (
    save_cycle, 
    get_user_cycles, 
    predict_next_period, 
    render_monthly_calendar,
    render_cycle_chart
)
from modules.health_data import render_water_tracker, render_exercise_guide
from modules.translations import translations

# Page Config
st.set_page_config(
    page_title="Mahwari ka Trekr",
    page_icon="assets/icon-192x192.png",
    layout="centered",
    initial_sidebar_state="collapsed"
)
# Initialize DB
init_db()

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def inject_custom_css(hue):
    # Dynamic Hue Injection
    css = f"""
    <style>
        :root {{
            --primary-color: hsl({hue}, 100%, 50%);
            --primary-dark: hsl({hue}, 100%, 30%);
            --primary-light: hsl({hue}, 100%, 70%);
        }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        
    if "show_settings" not in st.session_state:
        st.session_state["show_settings"] = False

    load_css("assets/style.css")
    
    # --- Video Assets Logic ---
    import base64
    def get_base64_video(video_path):
        try:
            with open(video_path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        except FileNotFoundError:
            return None

    # 1. Loading Screen
    if "has_loaded" not in st.session_state:
        loading_video = get_base64_video("assets/loading.mp4")
        if loading_video:
            st.markdown(f"""
            <style>
                .stApp {{ overflow: hidden; }}
                header {{ visibility: hidden; }}
            </style>
            <div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: black; z-index: 9999; display: flex; align-items: center; justify-content: center;">
                <video autoplay muted playsinline style="width: 100%; height: 100%; object-fit: cover;">
                    <source src="data:video/mp4;base64,{loading_video}" type="video/mp4">
                </video>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(5) # Play for 5 seconds
            st.session_state["has_loaded"] = True
            st.rerun()
        else:
             st.session_state["has_loaded"] = True

    # 2. Background Video
    bg_video = get_base64_video("assets/background.mp4")
    if bg_video:
        st.markdown(f"""
        <style>
            .stApp {{
                background: transparent;
            }}
            .video-bg {{
                position: fixed;
                right: 0;
                bottom: 0;
                min-width: 100%; 
                min-height: 100%;
                z-index: -1;
                object-fit: cover;
                opacity: 80; /* Slight Transparency */
            }}
            .overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.6); /* Dark Overlay for text readability */
                z-index: -1;
            }}
        </style>
        <video autoplay loop muted playsinline class="video-bg">
            <source src="data:video/mp4;base64,{bg_video}" type="video/mp4">
        </video>
        <div class="overlay"></div>
        """, unsafe_allow_html=True)

    if not st.session_state["authenticated"]:
        render_auth()
    else:
        username = st.session_state["username"]
        settings = get_user_settings(username)
        hue = settings.get('hue', 0)
        lang = settings.get('language', 'en')
        t = translations.get(lang, translations['en'])
        
        # Language Display Mapping
        LANG_NAMES = {
            "en": "English",
            "ta": "Tamil (தமிழ்)",
            "ml": "Malayalam (മലയാളം)",
            "ur": "Urdu (اردو)",
            "te": "Telugu (తెలుగు)",
            "bn": "Bengali (বাংলা)",
            "or": "Odia (ଓଡ଼ିଆ)",
            "kn": "Kannada (ಕನ್ನಡ)",
            "mr": "Marathi (मराठी)",
            "hi": "Hindi (हिंदी)",
            "ne": "Nepali (नेपाली)"
        }
        
        inject_custom_css(hue)
        
        # --- Top Bar Navigation ---
        # Push settings button to absolute right using narrow column
        col1, col2 = st.columns([12, 1])
        
        with col1:
             st.markdown(f"<h2 style='margin:0; padding-top:10px;'>🌸 {t['welcome']}, {username}!</h2>", unsafe_allow_html=True)
        
        with col2:
            # Settings Toggle Button (Aligned to right)
            if st.button("⚙️", key="settings_btn", help=t.get('settings', "Settings")):
                st.session_state["show_settings"] = not st.session_state["show_settings"]
                st.rerun()

        # --- Settings Overlay ---
        if st.session_state["show_settings"]:
            st.markdown('<div class="settings-overlay">', unsafe_allow_html=True)
            st.markdown(f"### {t['settings']}")
            
            # Hue Slider
            new_hue = st.slider(t['theme_color'], 0, 360, hue, help=t['adjust_theme'])
            if new_hue != hue:
                update_user_setting(username, 'hue', new_hue)
                st.rerun()

            # Language
            lang_opts = list(translations.keys())
            new_lang = st.selectbox(
                t['language'], 
                lang_opts, 
                index=lang_opts.index(lang) if lang in lang_opts else 0,
                format_func=lambda x: LANG_NAMES.get(x, x)
            )
            if new_lang != lang:
               update_user_setting(username, 'language', new_lang)
               st.rerun()
            
            # Change PIN Section
            st.markdown("---")
            st.subheader(t['change_pin'])
            with st.form("change_pin_form"):
                old_pin = st.text_input(t.get('security_pin', "Old PIN"), type="password", max_chars=6, key="old_p")
                new_pin = st.text_input(t.get('change_pin', "New PIN"), type="password", max_chars=6, key="new_p")
                
                if st.form_submit_button(t['change_pin']):
                    if len(new_pin) < 6:
                        st.error("PIN must be 6 digits")
                    else:
                        success, msg = change_pin(username, old_pin, new_pin)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
            
            st.markdown("---")
            if st.button(t['logout'], key="logout_btn", use_container_width=True):
                st.session_state.clear()
                st.rerun()
                
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Dashboard Content ---
        
        # Tabs: Log Period (First), Tracker, Health
        # Updated Labels with Emojis
        tab_log, tab_dash, tab_health = st.tabs([f"🩸 {t['log_period']}", f"📊 {t['tab_tracker']}", f"💪 {t['tab_health']}"])
        
        cycles = get_user_cycles(username)
        predicted_date = predict_next_period(cycles)
        
        with tab_dash:
            # Prediction Logic
            if predicted_date:
                days_left = (predicted_date - date.today()).days
                msg = f"{t['predicted_next']}: **{days_left}** days (**{predicted_date.strftime('%d %b %Y')}**)"
                if days_left < 0:
                    msg = f"{t['predicted_next']}: **{predicted_date.strftime('%d %b %Y')}** ({abs(days_left)} days ago)"
                st.info(msg)
            
            # Chart
            st.markdown(f"### {t['cycle_analysis']}")
            fig_chart = render_cycle_chart(cycles)
            if fig_chart:
                st.plotly_chart(fig_chart, use_container_width=True)
            else:
                st.info(t.get('note', 'No data available'))

            # Record History Table
            if not cycles.empty:
                 st.markdown("---")
                 with st.expander(t['view_table']):
                    st.dataframe(cycles.sort_values("start_date", ascending=False), use_container_width=True)


        with tab_log:
            st.subheader(t['log_period'])
            
            # Show prediction here too
            if predicted_date:
                days_left = (predicted_date - date.today()).days
                msg = f"{t['predicted_next']}: **{days_left}** days (**{predicted_date.strftime('%d %b %Y')}**)"
                if days_left < 0:
                    msg = f"{t['predicted_next']}: **{predicted_date.strftime('%d %b %Y')}** ({abs(days_left)} days ago)"
                st.info(msg)

            with st.form("cycle_form"):
                today_max = datetime.today()
                start_d = st.date_input(t['start_date'], max_value=today_max, format="DD/MM/YYYY")
                end_d = st.date_input(t['end_date'], max_value=today_max, format="DD/MM/YYYY")
                
                if st.form_submit_button(t['save_cycle']):
                    if end_d < start_d:
                        st.error(t['date_error'])
                    else:
                        save_cycle(username, start_d, end_d)
                        st.success(t['cycle_saved_msg'])
                        st.rerun()

        with tab_health:
            render_water_tracker(t)
            st.markdown("---")
            render_exercise_guide(t)

if __name__ == "__main__":
    main()
