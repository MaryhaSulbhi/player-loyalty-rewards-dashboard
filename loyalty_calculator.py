import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class LoyaltyCalculator:
    """
    Loyalty Points Calculator for ABC Gaming Platform.
    
    Formula: LP = (0.01 * deposit) + (0.005 * withdrawal) + 
                  (0.001 * max(#deposits - #withdrawals, 0)) + 
                  (0.2 * games_played)
    """
    
    def __init__(self):
        
        self.weights = {
            'deposit_amount': 0.01,
            'withdrawal_amount': 0.005,
            'deposit_frequency': 0.001,
            'games_played': 0.2
        }
    
    def calculate_player_loyalty_points(self, player_data):
        """
        Calculate loyalty points for a single player's data.
        
        Args:
            player_data (pd.DataFrame): Player's activity data
            
        Returns:
            dict: Calculated loyalty points and breakdown
        """
        total_deposits = player_data['deposits'].sum()
        total_withdrawals = player_data['withdrawals'].sum()
        total_games = player_data['games_played'].sum()
        
        deposit_count = (player_data['deposits'] > 0).sum()
        withdrawal_count = (player_data['withdrawals'] > 0).sum()
        
        deposit_points = total_deposits * self.weights['deposit_amount']
        withdrawal_points = total_withdrawals * self.weights['withdrawal_amount']
        
        frequency_diff = max(deposit_count - withdrawal_count, 0)
        frequency_points = frequency_diff * self.weights['deposit_frequency']
        
        games_points = total_games * self.weights['games_played']
        
        total_points = deposit_points + withdrawal_points + frequency_points + games_points
        
        return {
            'total_loyalty_points': total_points,
            'deposit_points': deposit_points,
            'withdrawal_points': withdrawal_points,
            'frequency_points': frequency_points,
            'games_points': games_points,
            'total_deposits': total_deposits,
            'total_withdrawals': total_withdrawals,
            'total_games_played': total_games,
            'deposit_transactions': deposit_count,
            'withdrawal_transactions': withdrawal_count
        }
    
    def calculate_slot_loyalty_points(self, data, target_date, slot):
        """
        Calculate loyalty points for specific date and time slot.
        
        Args:
            data (pd.DataFrame): Player activity data
            target_date (str): Date in YYYY-MM-DD format
            slot (str): Time slot ('S1' or 'S2')
            
        Returns:
            pd.DataFrame: Player-wise loyalty points for the slot
        """
        slot_data = data[
            (data['date'].dt.strftime('%Y-%m-%d') == target_date) & 
            (data['time_slot'] == slot)
        ]
        
        if slot_data.empty:
            return pd.DataFrame()
        
        results = []
        
        for player_id in slot_data['player_id'].unique():
            player_slot_data = slot_data[slot_data['player_id'] == player_id]
            loyalty_calc = self.calculate_player_loyalty_points(player_slot_data)
            
            result = {
                'player_id': player_id,
                'date': target_date,
                'time_slot': slot,
                **loyalty_calc
            }
            results.append(result)
        
        return pd.DataFrame(results)
    
    def calculate_monthly_loyalty_points(self, data):
        """
        Calculate monthly loyalty points for all players.
        
        Args:
            data (pd.DataFrame): Monthly player activity data
            
        Returns:
            pd.DataFrame: Player-wise monthly loyalty points
        """
        results = []
        
        for player_id in data['player_id'].unique():
            player_data = data[data['player_id'] == player_id]
            loyalty_calc = self.calculate_player_loyalty_points(player_data)
            
            result = {
                'player_id': player_id,
                **loyalty_calc
            }
            results.append(result)
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('total_loyalty_points', ascending=False).reset_index(drop=True)
        
        return results_df
    
    def calculate_specific_slots_loyalty_points(self, data, slot_configs):
        """
        Calculate loyalty points for specific date-slot combinations.
        
        Args:
            data (pd.DataFrame): Player activity data
            slot_configs (list): List of {'date': 'YYYY-MM-DD', 'slot': 'S1/S2'} configs
            
        Returns:
            dict: Results for each slot configuration
        """
        results = {}
        
        for config in slot_configs:
            slot_key = f"{config['date']}_{config['slot']}"
            slot_results = self.calculate_slot_loyalty_points(
                data, config['date'], config['slot']
            )
            results[slot_key] = slot_results
        
        return results
    
    def rank_players_by_loyalty_points(self, loyalty_data, tie_breaker='total_games_played'):
        """
        Rank players by loyalty points with tie-breaking logic.
        
        Args:
            loyalty_data (pd.DataFrame): Player loyalty points data
            tie_breaker (str): Column to use for tie-breaking
            
        Returns:
            pd.DataFrame: Ranked player data
        """
        ranked_data = loyalty_data.sort_values(
            ['total_loyalty_points', tie_breaker], 
            ascending=[False, False]
        ).reset_index(drop=True)
        
        ranked_data['rank'] = range(1, len(ranked_data) + 1)
        
        return ranked_data
    
    def calculate_average_statistics(self, data):
        """
        Calculate average statistics from player data.
        
        Args:
            data (pd.DataFrame): Player activity data
            
        Returns:
            dict: Average statistics
        """
        stats = {
            'average_deposit_amount': data['deposits'].mean(),
            'average_deposit_per_user_per_month': data.groupby('player_id')['deposits'].sum().mean(),
            'average_games_played_per_user': data.groupby('player_id')['games_played'].sum().mean(),
            'total_unique_players': data['player_id'].nunique(),
            'total_deposits': data['deposits'].sum(),
            'total_withdrawals': data['withdrawals'].sum(),
            'total_games_played': data['games_played'].sum()
        }
        
        return stats
