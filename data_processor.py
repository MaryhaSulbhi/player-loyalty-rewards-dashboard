import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st

class DataProcessor:
    """
    Data processing utilities for ABC Gaming loyalty calculator.
    """
    
    def __init__(self):
        self.required_columns = [
            'player_id', 'date', 'time_slot', 'deposits', 'withdrawals', 'games_played'
        ]
    
    def load_data(self, uploaded_file):
        """
        Load and preprocess uploaded data file.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            pd.DataFrame: Processed data
        """
        try:
            if uploaded_file.name.endswith('.csv'):
                data = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                data = pd.read_excel(uploaded_file)
            else:
                raise ValueError("Unsupported file format. Please upload CSV or Excel files.")
            
            data = self.preprocess_data(data)
            
            return data
            
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
    
    def preprocess_data(self, data):
        """
        Preprocess and clean the data.
        
        Args:
            data (pd.DataFrame): Raw data
            
        Returns:
            pd.DataFrame: Cleaned data
        """
        data = data.copy()
        
        data.columns = data.columns.str.lower().str.strip()
        
        missing_columns = set(self.required_columns) - set(data.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        try:
            data['date'] = pd.to_datetime(data['date'])
        except Exception:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD format.")
        
        valid_slots = ['S1', 'S2']
        invalid_slots = data[~data['time_slot'].isin(valid_slots)]['time_slot'].unique()
        if len(invalid_slots) > 0:
            raise ValueError(f"Invalid time_slot values: {invalid_slots}. Use 'S1' or 'S2'.")
        
        numeric_columns = ['deposits', 'withdrawals', 'games_played']
        for col in numeric_columns:
            try:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            except Exception:
                raise ValueError(f"Error converting {col} to numeric values.")
        
        data[numeric_columns] = data[numeric_columns].fillna(0)
        
        for col in numeric_columns:
            if (data[col] < 0).any():
                raise ValueError(f"Negative values found in {col}. All values must be non-negative.")
        
        initial_count = len(data)
        data = data.drop_duplicates()
        if len(data) < initial_count:
            st.info(f"Removed {initial_count - len(data)} duplicate records.")
        
        data = data.sort_values(['player_id', 'date', 'time_slot']).reset_index(drop=True)
        
        return data
    
    def generate_sample_data(self, num_players=50, num_days=30):
        """
        Generate sample data for testing (only for development purposes).
        
        Args:
            num_players (int): Number of players
            num_days (int): Number of days
            
        Returns:
            pd.DataFrame: Sample data
        """
        np.random.seed(42)  
        
        data_records = []
        base_date = datetime(2023, 10, 1)
        
        for player_num in range(1, num_players + 1):
            player_id = f"P{player_num:03d}"
            
            for day in range(num_days):
                current_date = base_date + pd.Timedelta(days=day)
                
                for slot in ['S1', 'S2']:
                   
                    if np.random.random() < 0.7:
                        record = {
                            'player_id': player_id,
                            'date': current_date.strftime('%Y-%m-%d'),
                            'time_slot': slot,
                            'deposits': max(0, np.random.normal(500, 300)),
                            'withdrawals': max(0, np.random.normal(300, 200)),
                            'games_played': max(0, int(np.random.normal(3, 2)))
                        }
                        data_records.append(record)
        
        return pd.DataFrame(data_records)
    
    def validate_date_range(self, data, start_date=None, end_date=None):
        """
        Validate data within specified date range.
        
        Args:
            data (pd.DataFrame): Input data
            start_date (str): Start date (YYYY-MM-DD)
            end_date (str): End date (YYYY-MM-DD)
            
        Returns:
            pd.DataFrame: Filtered data
        """
        if start_date:
            start_date = pd.to_datetime(start_date)
            data = data[data['date'] >= start_date]
        
        if end_date:
            end_date = pd.to_datetime(end_date)
            data = data[data['date'] <= end_date]
        
        return data
    
    def get_data_summary(self, data):
        """
        Get summary statistics of the data.
        
        Args:
            data (pd.DataFrame): Input data
            
        Returns:
            dict: Summary statistics
        """
        summary = {
            'total_records': len(data),
            'unique_players': data['player_id'].nunique(),
            'date_range': {
                'start': data['date'].min().strftime('%Y-%m-%d'),
                'end': data['date'].max().strftime('%Y-%m-%d')
            },
            'total_deposits': data['deposits'].sum(),
            'total_withdrawals': data['withdrawals'].sum(),
            'total_games': data['games_played'].sum(),
            'average_deposits_per_player': data.groupby('player_id')['deposits'].sum().mean(),
            'average_games_per_player': data.groupby('player_id')['games_played'].sum().mean(),
            'time_slot_distribution': data['time_slot'].value_counts().to_dict()
        }
        
        return summary
