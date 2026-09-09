import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="Dota 2 Tournament Analytics",
    page_icon="🏆",
    layout="wide"
)

@st.cache_data
def load_data():
    data = {}
    files = {
        'team_stats': 'data/team_stats.csv',
        'match_results': 'data/match_results.csv',
        'winrates': 'data/winrates.csv',
        'advanced_stats': 'data/advanced_stats.csv',
        'tournament_metrics': 'data/tournament_metrics.csv'
    }
    for name, path in files.items():
        if os.path.exists(path):
            data[name] = pd.read_csv(path)
        else:
            data[name] = pd.DataFrame()
    return data

st.title("The International 2026")
st.markdown("---")

with st.spinner("Loading data..."):
    data = load_data()
    
    team_stats = data['team_stats']
    match_results = data['match_results']
    winrates = data['winrates']
    advanced_stats = data['advanced_stats']
    tournament_metrics = data['tournament_metrics']

    if not tournament_metrics.empty:
        total_matches = int(tournament_metrics['total_matches'].iloc[0])
        avg_duration = tournament_metrics['avg_duration_min'].iloc[0]
        radiant_win_rate = (tournament_metrics['radiant_wins'].iloc[0] / total_matches * 100) if total_matches > 0 else 0
        total_teams = int(tournament_metrics['total_teams'].iloc[0])
    else:
        total_matches = len(match_results) if not match_results.empty else 0
        avg_duration = match_results['duration_minutes'].mean() if not match_results.empty else 0
        radiant_win_rate = 50
        total_teams = len(team_stats) if not team_stats.empty else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Teams", total_teams)
with col2:
    st.metric("Matches", total_matches)
with col3:
    st.metric("Avg Duration", f"{avg_duration:.1f} min")
with col4:
    st.metric("Radiant Win Rate", f"{radiant_win_rate:.1f}%")

st.markdown("---")

st.subheader("Tournament Overview")

if not team_stats.empty:
    display_df = team_stats.copy()
    display_df.columns = ['Team', 'Match', 'Win', 'Lose', 'Win Rate']
    display_df['Win Rate'] = display_df['Win Rate'].apply(lambda x: f'{x:.1f}%')

    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        column_config={
            'Team': st.column_config.TextColumn("Team", width="medium"),
            'Match': st.column_config.NumberColumn("Match", width="small"),
            'Win': st.column_config.NumberColumn("W", width="small"),
            'Lose': st.column_config.NumberColumn("L", width="small"),
            'Win Rate': st.column_config.TextColumn("Win Rate %", width="small"),
        }
    )
else:
    st.info("No data available")

st.markdown("---")
st.subheader("Odds Movement")

if not winrates.empty and not match_results.empty:
    winrates_data = winrates.merge(
        match_results[['match_id', 'radiant_team', 'dire_team', 'winner']], 
        on='match_id', 
        how='left'
    )
    
    if not winrates_data.empty:
        match_options = winrates_data['match_id'].unique().tolist()
        match_options_sorted = sorted(match_options)
        
        st.write("Select match by ID or choose from list:")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            match_id_input = st.text_input(
                "Match ID",
                value="",
                placeholder="Enter match ID..."
            )
        
        with col2:
            match_info_dict = {
                row['match_id']: f"Match {row['match_id']}: {row['radiant_team']} vs {row['dire_team']}" 
                for _, row in winrates_data[['match_id', 'radiant_team', 'dire_team']].drop_duplicates().iterrows()
            }
            
            selected_match_from_list = st.selectbox(
                "Or select from list",
                match_options_sorted,
                format_func=lambda x: match_info_dict.get(x, f"Match {x}"),
                index=None
            )
        
        if match_id_input:
            try:
                selected_match = int(match_id_input)
                if selected_match not in match_options:
                    st.warning(f"⚠️ Match ID {selected_match} not found. Available: {min(match_options)} - {max(match_options)}")
                    selected_match = None
            except ValueError:
                st.warning("⚠️ Please enter a valid numeric Match ID")
                selected_match = None
        else:
            selected_match = selected_match_from_list
        
        if selected_match is None and match_options:
            selected_match = match_options_sorted[0]
            st.info(f"Showing first match: {selected_match}")
        
        if selected_match:
            match_data = winrates_data[winrates_data['match_id'] == selected_match].copy()
            
            if not match_data.empty:
                radiant_team = match_data['radiant_team'].iloc[0]
                dire_team = match_data['dire_team'].iloc[0]
                winner = match_data['winner'].iloc[0]
                
                match_data['odds'] = (match_data['win_rate'] - 0.5) * 200
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=match_data['minute'],
                    y=match_data['odds'],
                    mode='lines+markers',
                    name='Win probability',
                    line=dict(color='#2c3e50', width=3),
                    marker=dict(size=4, color='#2c3e50'),
                    hovertemplate='Minute: %{x}<br>Radiant advantage: %{y:.1f}%<extra></extra>'
                ))
                
                fig.add_trace(go.Scatter(
                    x=match_data['minute'],
                    y=match_data['odds'],
                    fill='tozeroy',
                    fillcolor='rgba(44, 62, 80, 0.2)',
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                
                fig.add_annotation(
                    x=0.02, y=0,
                    xref="paper", yref="y",
                    text="50/50",
                    showarrow=False,
                    font=dict(size=10, color="gray"),
                    yshift=5
                )
                
                fig.add_annotation(
                    x=0.02, y=0.95,
                    xref="paper", yref="paper",
                    text=f"🟢 {radiant_team} (Radiant)",
                    showarrow=False,
                    font=dict(size=12, color='#28a745'),
                    bgcolor="rgba(255,255,255,0.8)"
                )
                
                fig.add_annotation(
                    x=0.02, y=0.05,
                    xref="paper", yref="paper",
                    text=f"🔴 {dire_team} (Dire)",
                    showarrow=False,
                    font=dict(size=12, color='#dc3545'),
                    bgcolor="rgba(255,255,255,0.8)"
                )
                
                fig.add_annotation(
                    x=0.98, y=100,
                    xref="paper", yref="y",
                    text="Radiant 100%",
                    showarrow=False,
                    font=dict(size=10, color='#28a745'),
                    yshift=5
                )
                
                fig.add_annotation(
                    x=0.98, y=-100,
                    xref="paper", yref="y",
                    text="Dire 100%",
                    showarrow=False,
                    font=dict(size=10, color='#dc3545'),
                    yshift=-5
                )
                
                fig.update_layout(
                    title=f"Win probability: {radiant_team} vs {dire_team}",
                    xaxis_title="Minute",
                    yaxis_title="Win probability (%)",
                    xaxis=dict(
                        range=[0, max(match_data['minute']) + 1],
                        tickmode='linear',
                        dtick=5
                    ),
                    yaxis=dict(
                        range=[-105, 105],
                        tickmode='array',
                        tickvals=[-100, -75, -50, -25, 0, 25, 50, 75, 100],
                        ticktext=['Dire 100%', '', 'Dire 75%', '', '50/50', '', 'Radiant 75%', '', 'Radiant 100%']
                    ),
                    height=500,
                    hovermode='x unified',
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Match ID", selected_match)
                with col2:
                    st.metric("Duration", f"{len(match_data)} min")
                with col3:
                    st.metric("Winner", winner)
                with col4:
                    final_odds = match_data['odds'].iloc[-1]
                    final_winner = radiant_team if final_odds > 0 else dire_team if final_odds < 0 else "Tie"
                    st.metric("Final prediction", f"{abs(final_odds):.1f}%", delta=f"{final_winner}")
            else:
                st.warning(f"No win rate data available for match {selected_match}")
        else:
            st.info("Please select or enter a match ID")
    else:
        st.info("No win rate data available")
else:
    st.info("No data available")

st.markdown("---")
st.subheader("Team Advanced Statistics")

if not advanced_stats.empty:
    team_options = advanced_stats['team_name'].tolist()
    selected_team = st.selectbox(
        "Select team",
        team_options
    )
    
    team_data = advanced_stats[advanced_stats['team_name'] == selected_team].iloc[0]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Matches", f"{team_data['total_matches']:.0f}")
    with col2:
        st.metric("Win Rate", f"{team_data['win_rate']:.1f}%")
    with col3:
        win_loss = f"{team_data['total_wins']:.0f}-{team_data['total_losses']:.0f}"
        st.metric("W-L", win_loss)
    with col4:
        st.metric("KDA", f"{team_data['kda_ratio']:.2f}")
    with col5:
        st.metric("Avg GPM", f"{team_data['avg_gpm']:.0f}")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Match Stats")
        st.markdown(f"""
        **Total Matches:** {team_data['total_matches']:.0f}  
        **Wins:** {team_data['total_wins']:.0f}  
        **Losses:** {team_data['total_losses']:.0f}  
        **Win Rate:** {team_data['win_rate']:.1f}%  
        """)
        
        st.subheader("Duration")
        st.markdown(f"""
        **Average:** {team_data['avg_match_duration_min']:.1f} min  
        """)
    
    with col2:
        st.subheader("Side Stats")
        st.markdown(f"""
        **Radiant WR:** {team_data['radiant_win_rate']:.1f}%  
        **Dire WR:** {team_data['dire_win_rate']:.1f}%  
        """)
        
        st.subheader("Player Averages")
        st.markdown(f"""
        **K/D/A:** {team_data['avg_kills']:.1f}/{team_data['avg_deaths']:.1f}/{team_data['avg_assists']:.1f}  
        **KDA Ratio:** {team_data['kda_ratio']:.2f}  
        **GPM:** {team_data['avg_gpm']:.0f}  
        **XPM:** {team_data['avg_xpm']:.0f}  
        """)
    
    with col3:
        st.subheader("Damage & Farm")
        st.markdown(f"""
        **Hero Damage:** {team_data['avg_hero_damage']:,.0f}  
        **Tower Damage:** {team_data['avg_tower_damage']:,.0f}  
        **Last Hits:** {team_data['avg_last_hits']:.0f}  
        **Denies:** {team_data['avg_denies']:.1f}  
        """)
    
    st.markdown("---")
    
    st.subheader("Team Comparison")
    
    compare_metric = st.selectbox(
        "Select metric to compare",
        ['Win Rate', 'KDA Ratio', 'Avg GPM', 'Avg XPM', 'Avg Kills', 'Avg Hero Damage']
    )
    
    metric_map = {
        'Win Rate': 'win_rate',
        'KDA Ratio': 'kda_ratio',
        'Avg GPM': 'avg_gpm',
        'Avg XPM': 'avg_xpm',
        'Avg Kills': 'avg_kills',
        'Avg Hero Damage': 'avg_hero_damage'
    }
    
    col_name = metric_map[compare_metric]
    all_teams = advanced_stats.copy()
    colors = ['#e74c3c' if team == selected_team else '#2c3e50' for team in all_teams['team_name']]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=all_teams['team_name'],
        y=all_teams[col_name],
        text=all_teams[col_name].apply(lambda x: f'{x:.1f}' if isinstance(x, (int, float)) else ''),
        textposition='outside',
        marker_color=colors
    ))
    
    if col_name == 'win_rate':
        fig.update_traces(text=all_teams[col_name].apply(lambda x: f'{x:.1f}%'))
        y_title = 'Win Rate (%)'
    elif col_name == 'kda_ratio':
        y_title = 'KDA Ratio'
    else:
        y_title = compare_metric

    max_value = all_teams[col_name].max()
    
    fig.update_layout(
        title=f'{compare_metric} - All Teams',
        xaxis_title='Team',
        yaxis_title=y_title,
        yaxis=dict(range=[0, max_value * 1.15]),
        height=450,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
else:
    st.info("No team statistics available")

st.markdown("---")
st.caption(f"Data from TI 2026 • {total_matches} matches • {total_teams} teams")