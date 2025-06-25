import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
from loyalty_calculator import LoyaltyCalculator
from data_processor import DataProcessor
from utils import export_to_excel, validate_data


st.set_page_config(
    page_title="ABC Gaming - Loyalty Points Calculator",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)


if 'data' not in st.session_state:
    st.session_state.data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'loyalty_results' not in st.session_state:
    st.session_state.loyalty_results = None

def main():
    st.title("🎮 ABC Gaming - Loyalty Points Calculator")
    st.markdown("### Real-money Gaming Platform Loyalty Analysis Tool")
    
    
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["Data Upload", "Loyalty Calculations", "Rankings & Analysis", "Bonus Allocation", "Reports"]
    )
    
    if page == "Data Upload":
        data_upload_page()
    elif page == "Loyalty Calculations":
        loyalty_calculations_page()
    elif page == "Rankings & Analysis":
        rankings_analysis_page()
    elif page == "Bonus Allocation":
        bonus_allocation_page()
    elif page == "Reports":
        reports_page()

def data_upload_page():
    st.header("📁 Data Upload & Processing")
    
    
    st.subheader("Upload Player Activity Data")
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload player activity data with columns: player_id, date, time_slot, deposits, withdrawals, games_played"
    )
    
    if uploaded_file is not None:
        try:
           
            processor = DataProcessor()
            data = processor.load_data(uploaded_file)
            
            st.success(f"✅ File uploaded successfully! Found {len(data)} records.")
            
            
            st.subheader("Data Preview")
            st.dataframe(data.head(10), use_container_width=True)
            
            
            validation_results = validate_data(data)
            if validation_results['is_valid']:
                st.success("✅ Data validation passed!")
                st.session_state.data = data
                
                st.subheader("Data Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Players", data['player_id'].nunique())
                with col2:
                    st.metric("Total Records", len(data))
                with col3:
                    st.metric("Date Range", f"{data['date'].min()} to {data['date'].max()}")
                with col4:
                    st.metric("Total Deposits", f"₹{data['deposits'].sum():,.2f}")
                    
            else:
                st.error("❌ Data validation failed!")
                for error in validation_results['errors']:
                    st.error(f"• {error}")
                    
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
    
    with st.expander("📋 Expected Data Format"):
        st.markdown("""
        **Required Columns:**
        - `player_id`: Unique identifier for each player
        - `date`: Date of activity (YYYY-MM-DD format)
        - `time_slot`: S1 (12am-12pm) or S2 (12pm-12am)
        - `deposits`: Amount deposited by player
        - `withdrawals`: Amount withdrawn by player
        - `games_played`: Number of games played
        
        **Sample Data:**
        | player_id | date | time_slot | deposits | withdrawals | games_played |
        |-----------|------|-----------|----------|-------------|--------------|
        | P001 | 2023-10-02 | S1 | 1000 | 500 | 5 |
        | P001 | 2023-10-16 | S2 | 0 | 0 | 3 |
        """)

def loyalty_calculations_page():
    st.header("🧮 Loyalty Points Calculations")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please upload data first in the Data Upload page.")
        return
    
    st.subheader("Calculation Parameters")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **Loyalty Points Formula:**
        
        LP = (0.01 × Deposits) + (0.005 × Withdrawals) + 
             (0.001 × max(#Deposits - #Withdrawals, 0)) + 
             (0.2 × Games Played)
        """)
    
    with col2:
        selected_month = st.selectbox(
            "Select Month for Analysis",
            options=sorted(st.session_state.data['date'].dt.strftime('%Y-%m').unique()),
            help="Choose month for loyalty points calculation"
        )
    
    if st.button("🚀 Calculate Loyalty Points", type="primary"):
        with st.spinner("Calculating loyalty points..."):
            calculator = LoyaltyCalculator()
            
            month_data = st.session_state.data[
                st.session_state.data['date'].dt.strftime('%Y-%m') == selected_month
            ]
            
            loyalty_results = calculator.calculate_monthly_loyalty_points(month_data)
            st.session_state.loyalty_results = loyalty_results
            
            st.success("✅ Loyalty points calculated successfully!")
    
    if st.session_state.loyalty_results is not None:
        st.subheader("📊 Loyalty Points Results")
        
        results_df = st.session_state.loyalty_results
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Players", len(results_df))
        with col2:
            st.metric("Avg Loyalty Points", f"{results_df['total_loyalty_points'].mean():.2f}")
        with col3:
            st.metric("Max Loyalty Points", f"{results_df['total_loyalty_points'].max():.2f}")
        with col4:
            st.metric("Total Points Awarded", f"{results_df['total_loyalty_points'].sum():.2f}")
        
        st.subheader("Player-wise Loyalty Points")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            search_player = st.text_input("🔍 Search Player ID", placeholder="Enter player ID...")
        with col2:
            min_points = st.number_input("Min Points Filter", min_value=0.0, value=0.0)
        
        filtered_results = results_df.copy()
        if search_player:
            filtered_results = filtered_results[
                filtered_results['player_id'].str.contains(search_player, case=False, na=False)
            ]
        if min_points > 0:
            filtered_results = filtered_results[filtered_results['total_loyalty_points'] >= min_points]
        
        st.dataframe(
            filtered_results.sort_values('total_loyalty_points', ascending=False),
            use_container_width=True,
            column_config={
                "total_loyalty_points": st.column_config.NumberColumn(
                    "Total Loyalty Points",
                    format="%.2f"
                ),
                "total_deposits": st.column_config.NumberColumn(
                    "Total Deposits",
                    format="₹%.2f"
                ),
                "total_withdrawals": st.column_config.NumberColumn(
                    "Total Withdrawals",
                    format="₹%.2f"
                )
            }
        )

def rankings_analysis_page():
    st.header("🏆 Rankings & Statistical Analysis")
    
    if st.session_state.loyalty_results is None:
        st.warning("⚠️ Please calculate loyalty points first.")
        return
    
    results_df = st.session_state.loyalty_results
    
    st.subheader("🥇 Monthly Player Rankings")
    
    top_players = results_df.nlargest(50, 'total_loyalty_points').reset_index(drop=True)
    top_players['rank'] = range(1, len(top_players) + 1)
    
    st.markdown("**Top 10 Players:**")
    st.dataframe(
        top_players.head(10)[['rank', 'player_id', 'total_loyalty_points', 'total_deposits', 'total_games_played']],
        use_container_width=True,
        column_config={
            "rank": "Rank",
            "player_id": "Player ID",
            "total_loyalty_points": st.column_config.NumberColumn("Loyalty Points", format="%.2f"),
            "total_deposits": st.column_config.NumberColumn("Total Deposits", format="₹%.2f"),
            "total_games_played": "Games Played"
        },
        hide_index=True
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Loyalty Points Distribution")
        fig_hist = px.histogram(
            results_df, 
            x='total_loyalty_points',
            nbins=20,
            title="Distribution of Loyalty Points"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Top 20 Players")
        top_20 = results_df.nlargest(20, 'total_loyalty_points')
        fig_bar = px.bar(
            top_20,
            x='player_id',
            y='total_loyalty_points',
            title="Top 20 Players by Loyalty Points"
        )
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.subheader("📊 Statistical Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Deposit Statistics:**")
        st.metric("Average Deposit", f"₹{results_df['total_deposits'].mean():.2f}")
        st.metric("Median Deposit", f"₹{results_df['total_deposits'].median():.2f}")
        st.metric("Max Deposit", f"₹{results_df['total_deposits'].max():.2f}")
    
    with col2:
        st.markdown("**Withdrawal Statistics:**")
        st.metric("Average Withdrawal", f"₹{results_df['total_withdrawals'].mean():.2f}")
        st.metric("Median Withdrawal", f"₹{results_df['total_withdrawals'].median():.2f}")
        st.metric("Max Withdrawal", f"₹{results_df['total_withdrawals'].max():.2f}")
    
    with col3:
        st.markdown("**Gaming Statistics:**")
        st.metric("Average Games Played", f"{results_df['total_games_played'].mean():.1f}")
        st.metric("Median Games Played", f"{results_df['total_games_played'].median():.0f}")
        st.metric("Max Games Played", f"{results_df['total_games_played'].max():.0f}")
    
    st.subheader("🔗 Correlation Analysis")
    correlation_data = results_df[['total_deposits', 'total_withdrawals', 'total_games_played', 'total_loyalty_points']]
    
    fig_corr = px.imshow(
        correlation_data.corr(),
        text_auto=True,
        aspect="auto",
        title="Correlation Matrix"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

def bonus_allocation_page():
    st.header("💰 Bonus Allocation")
    
    if st.session_state.loyalty_results is None:
        st.warning("⚠️ Please calculate loyalty points first.")
        return
    
    results_df = st.session_state.loyalty_results
    
    st.subheader("💼 Bonus Pool Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        bonus_pool = st.number_input(
            "Total Bonus Pool (₹)",
            min_value=0.0,
            value=50000.0,
            step=1000.0,
            help="Enter the total bonus amount to be distributed"
        )
    
    with col2:
        allocation_method = st.selectbox(
            "Allocation Method",
            ["Proportional to Loyalty Points", "Equal Distribution", "Tiered Distribution"],
            help="Choose how to distribute the bonus among top 50 players"
        )
    
    top_50_players = results_df.nlargest(50, 'total_loyalty_points').reset_index(drop=True)
    top_50_players['rank'] = range(1, len(top_50_players) + 1)
    
    if st.button("💸 Calculate Bonus Allocation", type="primary"):
        if allocation_method == "Proportional to Loyalty Points":
            total_points = top_50_players['total_loyalty_points'].sum()
            top_50_players['bonus_amount'] = (
                top_50_players['total_loyalty_points'] / total_points * bonus_pool
            )
        
        elif allocation_method == "Equal Distribution":
            top_50_players['bonus_amount'] = bonus_pool / 50
        
        elif allocation_method == "Tiered Distribution":
            top_50_players['bonus_amount'] = 0.0
            
            top_10_bonus = bonus_pool * 0.5 / 10
            top_50_players.loc[:9, 'bonus_amount'] = top_10_bonus
            
            next_20_bonus = bonus_pool * 0.35 / 20
            top_50_players.loc[10:29, 'bonus_amount'] = next_20_bonus
            
            last_20_bonus = bonus_pool * 0.15 / 20
            top_50_players.loc[30:49, 'bonus_amount'] = last_20_bonus
        
        st.success("✅ Bonus allocation calculated successfully!")
        
        st.subheader("📋 Bonus Allocation Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Players", len(top_50_players))
        with col2:
            st.metric("Total Allocated", f"₹{top_50_players['bonus_amount'].sum():.2f}")
        with col3:
            st.metric("Average Bonus", f"₹{top_50_players['bonus_amount'].mean():.2f}")
        
        st.subheader("🏆 Top 50 Players - Bonus Allocation")
        
        display_columns = ['rank', 'player_id', 'total_loyalty_points', 'bonus_amount']
        st.dataframe(
            top_50_players[display_columns],
            use_container_width=True,
            column_config={
                "rank": "Rank",
                "player_id": "Player ID",
                "total_loyalty_points": st.column_config.NumberColumn("Loyalty Points", format="%.2f"),
                "bonus_amount": st.column_config.NumberColumn("Bonus Amount", format="₹%.2f")
            },
            hide_index=True
        )
        
        st.subheader("📊 Bonus Distribution Visualization")
        
        top_50_players['tier'] = pd.cut(
            top_50_players['rank'],
            bins=[0, 10, 30, 50],
            labels=['Top 10', 'Rank 11-30', 'Rank 31-50']
        )
        
        tier_summary = top_50_players.groupby('tier')['bonus_amount'].sum().reset_index()
        
        fig_pie = px.pie(
            tier_summary,
            values='bonus_amount',
            names='tier',
            title="Bonus Distribution by Tier"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.session_state.bonus_allocation = top_50_players

def reports_page():
    st.header("📊 Reports & Export")
    
    if st.session_state.loyalty_results is None:
        st.warning("⚠️ Please calculate loyalty points first.")
        return
    
    st.subheader("📋 Available Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Loyalty Points Report**")
        st.markdown("• Complete player loyalty points breakdown")
        st.markdown("• Monthly rankings and statistics")
        st.markdown("• Player activity summary")
        
        if st.button("📥 Download Loyalty Points Report"):
            export_data = {
                'Loyalty Points': st.session_state.loyalty_results,
                'Top 50 Rankings': st.session_state.loyalty_results.nlargest(50, 'total_loyalty_points')
            }
            
            excel_buffer = export_to_excel(export_data, "Loyalty_Points_Report")
            
            st.download_button(
                label="💾 Download Excel Report",
                data=excel_buffer,
                file_name=f"loyalty_points_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        st.markdown("**Bonus Allocation Report**")
        st.markdown("• Top 50 players bonus distribution")
        st.markdown("• Allocation methodology details")
        st.markdown("• Summary statistics")
        
        if hasattr(st.session_state, 'bonus_allocation') and st.button("📥 Download Bonus Report"):
            bonus_data = {
                'Bonus Allocation': st.session_state.bonus_allocation,
                'Summary': pd.DataFrame({
                    'Metric': ['Total Players', 'Total Bonus Pool', 'Average Bonus'],
                    'Value': [
                        len(st.session_state.bonus_allocation),
                        st.session_state.bonus_allocation['bonus_amount'].sum(),
                        st.session_state.bonus_allocation['bonus_amount'].mean()
                    ]
                })
            }
            
            excel_buffer = export_to_excel(bonus_data, "Bonus_Allocation_Report")
            
            st.download_button(
                label="💾 Download Bonus Report",
                data=excel_buffer,
                file_name=f"bonus_allocation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    st.subheader("📈 Executive Summary")
    
    results_df = st.session_state.loyalty_results
    
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.info(f"""
        **Player Engagement**
        - Total Active Players: {len(results_df)}
        - Average Games per Player: {results_df['total_games_played'].mean():.1f}
        - Most Active Player: {results_df.loc[results_df['total_games_played'].idxmax(), 'player_id']}
        """)
    
    with summary_col2:
        st.info(f"""
        **Financial Metrics**
        - Total Deposits: ₹{results_df['total_deposits'].sum():,.2f}
        - Total Withdrawals: ₹{results_df['total_withdrawals'].sum():,.2f}
        - Net Platform Revenue: ₹{(results_df['total_deposits'].sum() - results_df['total_withdrawals'].sum()):,.2f}
        """)
    
    with summary_col3:
        st.info(f"""
        **Loyalty Program**
        - Total Points Awarded: {results_df['total_loyalty_points'].sum():.0f}
        - Average Points per Player: {results_df['total_loyalty_points'].mean():.1f}
        - Top Performer: {results_df.loc[results_df['total_loyalty_points'].idxmax(), 'player_id']}
        """)

if __name__ == "__main__":
    main()
