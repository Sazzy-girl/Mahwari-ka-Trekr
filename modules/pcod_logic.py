import pandas as pd
import numpy as np

def calculate_pcod_risk(cycles_df):
    """
    Analyzes cycle data to estimate PCOD risk.
    Risk Factors:
    1. Irregular cycle lengths (high variance).
    2. Long cycles (> 35 days).
    3. Specifcally very short cycles (< 21 days).
    """
    if cycles_df.empty or len(cycles_df) < 3:
        return "Insufficient Data (Need 3+ cycles)", "gray"
    
    cycles_df['start_date'] = pd.to_datetime(cycles_df['start_date'])
    cycles_df = cycles_df.sort_values('start_date')
    
    cycles_df['prev_start'] = cycles_df['start_date'].shift(1)
    # Calculate cycle length (start to start)
    cycle_lengths = (cycles_df['start_date'] - cycles_df['prev_start']).dt.days.dropna()
    
    if len(cycle_lengths) == 0:
        return "Insufficient Data", "gray"
        
    avg_length = cycle_lengths.mean()
    std_dev = cycle_lengths.std()
    
    risk_score = 0
    reasons = []
    
    # Check for long cycles
    if avg_length > 35:
        risk_score += 2
        reasons.append("Average cycle length > 35 days")
    elif avg_length < 21:
        risk_score += 2
        reasons.append("Average cycle length < 21 days")
        
    # Check for irregularity
    if std_dev > 5: # High variance
        risk_score += 1
        reasons.append("Irregular cycle lengths")
    
    if risk_score >= 2:
        return "High Risk", "#ff4b4b" # Red
    elif risk_score == 1:
        return "Medium Risk", "#ffa500" # Orange
    else:
        return "Low Risk", "#00ff00" # Green
