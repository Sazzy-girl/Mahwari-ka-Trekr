import streamlit as st
import os

# Must be the first streamit command
st.set_page_config(
    page_title="Mahwari ka Trekr",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize DB
from modules.database_setup import init_db
init_db()

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Main App Logic
def main():
    if not st.session_state["authenticated"]:
        from modules.auth import render_auth
        render_auth()
    else:
        # Layout
        username = st.session_state.get('username', 'User')
        
        # Sidebar
        with st.sidebar:
            st.title(f"🌸 Welcome, {username}!")
            st.markdown("---")
            if st.button("Logout", key="logout_btn"):
                st.session_state["authenticated"] = False
                st.rerun()
        
        # Main Dashboard
        st.markdown("<h1 style='text-align: center; color: #ff69b4;'>Mahwari ka Trekr</h1>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📅 Tracker", "📊 Analytics", "🧘‍♀️ Health"])
        
        # Imports
        from modules.calendar_logic import save_cycle, get_user_cycles, predict_next_period, render_calendar_plot, render_cycle_chart
        from modules.pcod_logic import calculate_pcod_risk
        from modules.health_data import render_water_tracker, render_exercise_guide
        
        # Fetch Data
        cycles = get_user_cycles(username)
        predicted_date = predict_next_period(cycles)
        
        with tab1:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("Log Period")
                with st.form("cycle_form"):
                    start_d = st.date_input("Start Date")
                    end_d = st.date_input("End Date")
                    
                    if st.form_submit_button("Save Cycle"):
                        if end_d < start_d:
                            st.error("End date cannot be before start date.")
                        else:
                            save_cycle(username, start_d, end_d)
                            st.success("Cycle logged!")
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
                if predicted_date:
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 5px solid #ff0000;">
                        <h3>Predicted Next Period</h3>
                        <h2 style="color: #ff4b4b;">{predicted_date}</h2>
                        <p style="font-size: 0.8em; color: gray;">Based on your average cycle.</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                fig_cal = render_calendar_plot(cycles, predicted_date)
                st.plotly_chart(fig_cal, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            st.subheader("Cycle Analysis")
            
            risk, color = calculate_pcod_risk(cycles)
            st.markdown(f"""
            <div class="glass-card" style="text-align: center;">
                <h2>PCOD Risk Assessment</h2>
                <h1 style="color: {color}; font-size: 3em;">{risk}</h1>
                <p>Based on cycle regularity and duration.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            fig_chart = render_cycle_chart(cycles)
            st.plotly_chart(fig_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.expander("View Data Table"):
                st.dataframe(cycles)

        with tab3:
            col_h1, col_h2 = st.columns(2)
            with col_h1:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                render_water_tracker()
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_h2:
                render_exercise_guide()

if __name__ == "__main__":
    main()
