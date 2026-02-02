import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from .database_setup import get_connection

def save_cycle(username, start_date, end_date):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO cycles (username, start_date, end_date) VALUES (?, ?, ?)", 
              (username, str(start_date), str(end_date)))
    conn.commit()
    conn.close()

def get_user_cycles(username):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM cycles WHERE username = ?", conn, params=(username,))
    conn.close()
    return df

def predict_next_period(cycles_df):
    if cycles_df.empty:
        return None
    
    # Calculate average cycle length if multiple cycles exist
    # For simplicity, if only one cycle, assume 28 days
    # Need at least 2 start dates to calculate cycle length
    cycles_df['start_date'] = pd.to_datetime(cycles_df['start_date'])
    cycles_df = cycles_df.sort_values('start_date')
    
    last_start = cycles_df.iloc[-1]['start_date']
    
    if len(cycles_df) < 2:
        avg_cycle = 28
    else:
        # Calculate diff between consecutive start dates
        cycles_df['prev_start'] = cycles_df['start_date'].shift(1)
        cycles_df['cycle_length'] = (cycles_df['start_date'] - cycles_df['prev_start']).dt.days
        avg_cycle = cycles_df['cycle_length'].mean()
    
    next_date = last_start + timedelta(days=int(avg_cycle))
    return next_date.date()

def render_calendar_plot(cycles_df, predicted_date):
    # Generate a date range for the current month/view
    # For this visual, let's show the current month + next month
    today = datetime.now().date()
    start_view = today.replace(day=1)
    end_view = (start_view + timedelta(days=60)) # Roughly 2 months
    
    dates = pd.date_range(start_view, end_view).to_list()
    
    # Prepare data for scatter plot (Calendar Grid)
    # x = Day of Week, y = Week Number (approx)
    
    plot_data = []
    
    # Existing Periods
    period_dates = []
    if not cycles_df.empty:
        for index, row in cycles_df.iterrows():
            s = pd.to_datetime(row['start_date']).date()
            e = pd.to_datetime(row['end_date']).date()
            # Expand range
            curr = s
            while curr <= e:
                period_dates.append(curr)
                curr += timedelta(days=1)
                
    for d in dates:
        color = 'lightgrey'
        size = 10
        text = str(d.day)
        
        if d.date() in period_dates:
            color = '#ff69b4' # Pink for actual period
            size = 15
        elif predicted_date and d.date() == predicted_date:
            color = '#ff0000' # Red for predicted
            size = 15
        
        # Grid position
        # week number relative to start_view
        week_num = int((d - pd.Timestamp(start_view)).days / 7)
        day_of_week = d.dayofweek # 0=Mon, 6=Sun
        
        plot_data.append({
            'date': d.date(),
            'week': -week_num, # Negative to stack downwards
            'day': day_of_week,
            'color': color,
            'size': size,
            'text': text
        })
        
    df_plot = pd.DataFrame(plot_data)
    
    fig = go.Figure(data=go.Scatter(
        x=df_plot['day'],
        y=df_plot['week'],
        mode='markers+text',
        marker=dict(
            size=30,
            color=df_plot['color'],
            symbol='circle',
            line=dict(width=1, color='white')
        ),
        text=df_plot['text'],
        textfont=dict(color='white'),
        hovertext=df_plot['date'].astype(str)
    ))
    
    fig.update_layout(
        title="Cycle Calendar",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickmode='array',
            tickvals=[0, 1, 2, 3, 4, 5, 6],
            ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            showgrid=False,
            zeroline=False,
            showticklabels=True
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        height=400,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def render_cycle_chart(cycles_df):
    if cycles_df.empty:
        return go.Figure()
    
    cycles_df['start_date'] = pd.to_datetime(cycles_df['start_date'])
    cycles_df['end_date'] = pd.to_datetime(cycles_df['end_date'])
    cycles_df['duration'] = (cycles_df['end_date'] - cycles_df['start_date']).dt.days + 1
    cycles_df['month'] = cycles_df['start_date'].dt.strftime('%B %Y')
    
    fig = go.Figure(data=[
        go.Bar(name='Duration', x=cycles_df['month'], y=cycles_df['duration'], marker_color='#ff69b4'),
        go.Scatter(name='Trend', x=cycles_df['month'], y=cycles_df['duration'], mode='lines+markers', line=dict(color='white'))
    ])
    
    fig.update_layout(
        title="Cycle Duration History",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        yaxis_title="Days"
    )
    return fig
