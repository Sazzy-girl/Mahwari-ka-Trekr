import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import calendar
import plotly.figure_factory as ff

def save_cycle(username, start_date, end_date):
    from .database_setup import get_connection
    conn = get_connection()
    c = conn.cursor()
    # Updated to store duration for PCOD logic
    duration = (end_date - start_date).days + 1
    c.execute("INSERT INTO cycles (username, start_date, end_date, duration) VALUES (?, ?, ?, ?)", 
              (username, str(start_date), str(end_date), duration))
    conn.commit()
    conn.close()

def get_user_cycles(username):
    from .database_setup import get_connection
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM cycles WHERE username = ?", conn, params=(username,))
    conn.close()
    return df

def predict_next_period(cycles_df):
    if cycles_df.empty:
        return None
    # Simple logic: Average cycle length or default 28
    # Needed: Start date of last cycle + 28 days
    last_cycle = cycles_df.iloc[-1]
    last_start = datetime.strptime(last_cycle['start_date'], '%Y-%m-%d').date()
    
    # Calculate average cycle length if enough data
    avg_length = 28
    if len(cycles_df) > 1:
        # Sort by date
        cycles_df['start_date'] = pd.to_datetime(cycles_df['start_date'])
        cycles_df = cycles_df.sort_values('start_date')
        
        diffs = cycles_df['start_date'].diff().dt.days.dropna()
        if not diffs.empty:
            avg_length = int(diffs.mean())
    
    next_date = last_start + timedelta(days=avg_length)
    return next_date

def render_calendar_plot(cycles_df, predicted_date):
    # This function is now deprecated in favor of render_monthly_calendar
    # But keeping empty return to avoid import errors if called elsewhere before update
    return {}

def render_cycle_chart(cycles_df):
    if cycles_df.empty:
        return None
    
    import plotly.graph_objects as go
    
    # Prepare Data
    df = cycles_df.copy()
    
    # Normalize dates
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])
    
    # Calculate Duration and Month key for merging
    df['duration'] = (df['end_date'] - df['start_date']).dt.days + 1
    df['month_dt'] = df['start_date'].dt.to_period('M').dt.to_timestamp()
    
    # Generate full range of months
    min_date = df['month_dt'].min()
    max_date = df['month_dt'].max()
    full_range = pd.date_range(start=min_date, end=max_date, freq='MS')
    
    df_full = pd.DataFrame({'month_dt': full_range})
    
    # Merge to keep all months
    merged = pd.merge(df_full, df, on='month_dt', how='left')
    
    # Fill Nans
    merged['duration'] = merged['duration'].fillna(0)
    merged['start_date'] = merged['start_date'].fillna(merged['month_dt']) # Just for hover stability if needed
    merged['end_date'] = merged['end_date'].fillna(merged['month_dt'])
    
    merged['month_label'] = merged['month_dt'].dt.strftime('%B %Y')
    
    # Separate loops for hover text handling to avoid errors on NaNs
    def build_hover(row):
        if row['duration'] == 0:
            return "No Data"
        return (
            "Start: " + row['start_date'].strftime('%d/%m/%Y') + "<br>" +
            "End: " + row['end_date'].strftime('%d/%m/%Y') + "<br>" +
            "Duration: " + str(int(row['duration'])) + " days"
        )
    
    merged['hover_text'] = merged.apply(build_hover, axis=1)

    fig = go.Figure(data=[
        go.Bar(
            x=merged['month_label'], 
            y=merged['duration'], 
            marker_color='#ff4081',
            # text=merged['duration'],  <-- Removed as requested
            # textposition='auto',      <-- Removed as requested
            hovertext=merged['hover_text'],
            hoverinfo="text"
        )
    ])
    
    fig.update_layout(
        title="Cycle Duration History",
        xaxis_title="Month",
        yaxis_title="Duration (Days)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        margin=dict(l=10, r=10, t=30, b=10),
        autosize=True,
        height=300
    )
    return fig

def render_monthly_calendar(cycles_df, predicted_date):
    # Modern CSS Grid Calendar
    today = datetime.today().date()
    
    # Navigation State
    if "cal_year" not in st.session_state:
        st.session_state["cal_year"] = today.year
        st.session_state["cal_month"] = today.month

    year = st.session_state["cal_year"]
    month = st.session_state["cal_month"]
    
    # Header logic
    col_prev, col_title, col_next = st.columns([1, 5, 1])
    with col_prev:
        if st.button("◀", key="prev_month"):
            if month == 1:
                st.session_state["cal_month"] = 12
                st.session_state["cal_year"] -= 1
            else:
                st.session_state["cal_month"] -= 1
            st.rerun()
            
    with col_title:
        month_name = calendar.month_name[month]
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{month_name} {year}</h3>", unsafe_allow_html=True)
        
    with col_next:
        if st.button("▶", key="next_month"):
            if month == 12:
                st.session_state["cal_month"] = 1
                st.session_state["cal_year"] += 1
            else:
                st.session_state["cal_month"] += 1
            st.rerun()
    
    # Data Processing
    period_days = set()
    if not cycles_df.empty:
        temp_df = cycles_df.copy()
        temp_df['start_date'] = pd.to_datetime(temp_df['start_date'])
        temp_df['end_date'] = pd.to_datetime(temp_df['end_date'])
        
        for index, row in temp_df.iterrows():
            s = row['start_date'].date()
            e = row['end_date'].date()
            curr = s
            while curr <= e:
                period_days.add(curr)
                curr += timedelta(days=1)

    # Calendar Construction
    cal = calendar.monthcalendar(year, month)
    days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    
    html = """
    <style>
        .modern-calendar {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 8px;
            margin-top: 15px;
            font-family: 'Outfit', sans-serif;
        }
        
        .cal-header {
            text-align: center;
            font-size: 0.85em;
            color: #888;
            font-weight: 600;
            padding-bottom: 5px;
        }
        
        .cal-cell {
            aspect-ratio: 1 / 1; /* Perfect squares */
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            padding: 5px;
            position: relative;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .cal-cell:hover {
            transform: translateY(-5px) scale(1.05);
            background: rgba(255, 255, 255, 0.15);
            border-color: rgba(255, 255, 255, 0.4);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            z-index: 2;
        }
        
        .day-num {
            font-size: 0.9em;
            font-weight: 500;
            margin-bottom: 2px;
        }
        
        .dot-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            width: 100%;
        }
        
        /* Variants */
        .is-empty {
            background: transparent;
            border: none;
            cursor: default;
        }
        .is-empty:hover {
            transform: none;
            background: transparent;
        }
        
        .is-period {
            background: rgba(255, 64, 129, 0.25);
            border-color: #ff4081;
            box-shadow: 0 0 10px rgba(255, 64, 129, 0.2);
        }
        
        .is-predicted {
            background: rgba(255, 80, 80, 0.15);
            border-color: #ff5050;
            border-style: dashed;
        }
        
        .is-today {
            border: 2px solid #00c6ff;
            background: rgba(0, 198, 255, 0.1);
        }
        
        .period-mark {
            font-size: 1.5rem;
            line-height: 1;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        /* Mobile adjustment */
        @media (max-width: 600px) {
            .modern-calendar { gap: 4px; }
            .cal-cell { border-radius: 8px; padding: 2px; }
            .day-num { font-size: 0.75em; }
            .period-mark { font-size: 1.2rem; }
        }
    </style>
    
    <div class="modern-calendar">
    """
    
    # Add Headers
    for day in days:
        html += f'<div class="cal-header">{day}</div>'
        
    # Add Days
    for week in cal:
        for day in week:
            if day == 0:
                html += '<div class="cal-cell is-empty"></div>'
                continue
            
            d_date = date(year, month, day)
            
            # Logic
            classes = ["cal-cell"]
            content = ""
            
            if d_date in period_days:
                classes.append("is-period")
                content = '<span class="period-mark">🩸</span>'
            elif predicted_date and d_date == predicted_date:
                classes.append("is-predicted")
                content = '<span style="font-size:0.7em; color:#ffaaaa;">Est.</span>'
            elif d_date == today:
                classes.append("is-today")
            
            html += f"""
            <div class="{' '.join(classes)}">
                <span class="day-num">{day}</span>
                <div class="dot-container">{content}</div>
            </div>
            """
            
    html += "</div>"
    
    # Legend
    legend = """
    <div style="display: flex; gap: 15px; justify-content: center; margin-top: 15px; font-size: 0.8em; color: #aaa;">
        <div style="display: flex; align-items: center; gap: 5px;">
            <div style="width: 10px; height: 10px; background: rgba(255, 64, 129, 0.5); border: 1px solid #ff4081; border-radius: 50%;"></div>
            <span>Period</span>
        </div>
        <div style="display: flex; align-items: center; gap: 5px;">
            <div style="width: 10px; height: 10px; background: rgba(255, 80, 80, 0.3); border: 1px dashed #ff5050; border-radius: 50%;"></div>
            <span>Predicted</span>
        </div>
        <div style="display: flex; align-items: center; gap: 5px;">
            <div style="width: 10px; height: 10px; border: 2px solid #00c6ff; border-radius: 50%;"></div>
            <span>Today</span>
        </div>
    </div>
    """
    st.markdown(html + legend, unsafe_allow_html=True)
