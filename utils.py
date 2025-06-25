import pandas as pd
import numpy as np
import io
from datetime import datetime
import streamlit as st

def validate_data(data):
    """
    Validate uploaded data for completeness and correctness.
    
    Args:
        data (pd.DataFrame): Input data to validate
        
    Returns:
        dict: Validation results with status and errors
    """
    errors = []
    
    required_columns = ['player_id', 'date', 'time_slot', 'deposits', 'withdrawals', 'games_played']
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
    
    if len(data) == 0:
        errors.append("Dataset is empty")
        return {'is_valid': False, 'errors': errors}
    
    if 'player_id' in data.columns:
        if data['player_id'].isnull().any():
            errors.append("Player ID contains null values")
    
    if 'date' in data.columns:
        try:
            pd.to_datetime(data['date'])
        except Exception:
            errors.append("Invalid date format detected")
    
    if 'time_slot' in data.columns:
        valid_slots = ['S1', 'S2']
        invalid_slots = data[~data['time_slot'].isin(valid_slots)]['time_slot'].unique()
        if len(invalid_slots) > 0:
            errors.append(f"Invalid time_slot values found: {list(invalid_slots)}")
    
    numeric_columns = ['deposits', 'withdrawals', 'games_played']
    for col in numeric_columns:
        if col in data.columns:
            try:
                numeric_data = pd.to_numeric(data[col], errors='coerce')
                if numeric_data.isnull().any():
                    errors.append(f"Non-numeric values found in {col}")
                if (numeric_data < 0).any():
                    errors.append(f"Negative values found in {col}")
            except Exception:
                errors.append(f"Error validating {col} column")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors
    }

def export_to_excel(data_dict, report_name):
    """
    Export multiple DataFrames to Excel with multiple sheets.
    
    Args:
        data_dict (dict): Dictionary of DataFrames {sheet_name: dataframe}
        report_name (str): Name of the report
        
    Returns:
        BytesIO: Excel file buffer
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, dataframe in data_dict.items():
            clean_sheet_name = sheet_name.replace('/', '_').replace('\\', '_')[:31]
            
            dataframe.to_excel(writer, sheet_name=clean_sheet_name, index=False)
            
            worksheet = writer.sheets[clean_sheet_name]
            
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    return output

def format_currency(amount):
    """
    Format amount as currency.
    
    Args:
        amount (float): Amount to format
        
    Returns:
        str: Formatted currency string
    """
    return f"₹{amount:,.2f}"

def format_number(number, decimal_places=2):
    """
    Format number with specified decimal places.
    
    Args:
        number (float): Number to format
        decimal_places (int): Number of decimal places
        
    Returns:
        str: Formatted number string
    """
    return f"{number:,.{decimal_places}f}"

def calculate_percentile_rank(series, value):
    """
    Calculate percentile rank of a value in a series.
    
    Args:
        series (pd.Series): Data series
        value (float): Value to find rank for
        
    Returns:
        float: Percentile rank (0-100)
    """
    return (series < value).sum() / len(series) * 100

def get_month_year_options(data):
    """
    Get unique month-year combinations from date column.
    
    Args:
        data (pd.DataFrame): Data with date column
        
    Returns:
        list: List of month-year strings (YYYY-MM format)
    """
    if 'date' not in data.columns:
        return []
    
    data['date'] = pd.to_datetime(data['date'])
    month_years = data['date'].dt.strftime('%Y-%m').unique()
    return sorted(month_years)

def filter_data_by_month(data, month_year):
    """
    Filter data by specific month-year.
    
    Args:
        data (pd.DataFrame): Input data
        month_year (str): Month-year in YYYY-MM format
        
    Returns:
        pd.DataFrame: Filtered data
    """
    data['date'] = pd.to_datetime(data['date'])
    return data[data['date'].dt.strftime('%Y-%m') == month_year]

def calculate_growth_rate(current_value, previous_value):
    """
    Calculate growth rate between two values.
    
    Args:
        current_value (float): Current period value
        previous_value (float): Previous period value
        
    Returns:
        float: Growth rate as percentage
    """
    if previous_value == 0:
        return 0 if current_value == 0 else 100
    
    return ((current_value - previous_value) / previous_value) * 100

def create_date_slot_key(date, slot):
    """
    Create a unique key for date-slot combination.
    
    Args:
        date (str): Date in YYYY-MM-DD format
        slot (str): Time slot (S1 or S2)
        
    Returns:
        str: Unique key
    """
    return f"{date}_{slot}"

def parse_date_slot_key(key):
    """
    Parse date-slot key back to components.
    
    Args:
        key (str): Date-slot key
        
    Returns:
        tuple: (date, slot)
    """
    parts = key.split('_')
    if len(parts) >= 2:
        date = '_'.join(parts[:-1])
        slot = parts[-1]
        return date, slot
    return None, None

def generate_loyalty_summary_report(loyalty_data):
    """
    Generate a summary report of loyalty points data.
    
    Args:
        loyalty_data (pd.DataFrame): Loyalty points data
        
    Returns:
        dict: Summary report
    """
    if loyalty_data.empty:
        return {}
    
    report = {
        'total_players': len(loyalty_data),
        'total_loyalty_points': loyalty_data['total_loyalty_points'].sum(),
        'average_loyalty_points': loyalty_data['total_loyalty_points'].mean(),
        'median_loyalty_points': loyalty_data['total_loyalty_points'].median(),
        'max_loyalty_points': loyalty_data['total_loyalty_points'].max(),
        'min_loyalty_points': loyalty_data['total_loyalty_points'].min(),
        'std_loyalty_points': loyalty_data['total_loyalty_points'].std(),
        'top_player': loyalty_data.loc[loyalty_data['total_loyalty_points'].idxmax(), 'player_id'],
        'total_deposits': loyalty_data['total_deposits'].sum(),
        'total_withdrawals': loyalty_data['total_withdrawals'].sum(),
        'total_games_played': loyalty_data['total_games_played'].sum(),
        'average_deposits_per_player': loyalty_data['total_deposits'].mean(),
        'average_games_per_player': loyalty_data['total_games_played'].mean()
    }
    
    return report
