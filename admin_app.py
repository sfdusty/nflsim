# admin_app.py

import streamlit as st
from admin.tasks import orchestrate_simulation_workflow
from app.dataviz import load_visualizations
import logging
import pandas as pd
import os
from io import BytesIO
from datetime import datetime
import glob
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_available_simulations(output_dir: str = 'data/simulations/') -> list:
    """
    Retrieves a list of available simulation identifiers based on CSV filenames.

    Args:
        output_dir (str): Directory where simulation CSV files are stored.

    Returns:
        list: List of available simulation identifiers.
    """
    files = glob.glob(os.path.join(output_dir, 'team_scores_*.csv'))
    simulations = []
    for file in files:
        filename = os.path.basename(file)
        # Updated regex to handle team names with underscores
        match = re.match(r'team_scores_([^_]+)_([^_]+)_(\d{8}_\d{6})\.csv', filename)
        if not match:
            logger.warning(f"Filename {filename} does not match expected pattern.")
            continue
        team1 = match.group(1)
        team2 = match.group(2)
        timestamp_str = match.group(3)
        try:
            timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        except ValueError:
            logger.warning(f"Timestamp {timestamp_str} in filename {filename} is invalid.")
            continue
        simulation_id = f"{team1} vs {team2} at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        # Define related file paths
        player_points_file = os.path.join(output_dir, f"player_points_{team1}_{team2}_{timestamp_str}.csv")
        player_percentiles_file = os.path.join(output_dir, f"player_percentiles_{team1}_{team2}_{timestamp_str}.csv")
        # Check if related files exist
        if not (os.path.exists(player_points_file) and os.path.exists(player_percentiles_file)):
            logger.warning(f"Related files for simulation {simulation_id} are missing.")
            continue
        simulations.append({
            'simulation_id': simulation_id,
            'team1': team1,
            'team2': team2,
            'timestamp': timestamp,
            'files': {
                'team_scores': file,
                'player_points': player_points_file,
                'player_percentiles': player_percentiles_file
            }
        })
    # Sort simulations by timestamp descending
    simulations = sorted(simulations, key=lambda x: x['timestamp'], reverse=True)
    return simulations

def convert_df_to_csv(df: pd.DataFrame) -> BytesIO:
    """
    Converts a DataFrame to a CSV bytes buffer.

    Args:
        df (pd.DataFrame): DataFrame to convert.

    Returns:
        BytesIO: Bytes buffer containing CSV data.
    """
    buffer = BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer

def main():
    st.set_page_config(page_title="NFL Simulator - Admin Panel", layout="wide")
    st.title("🏈 NFL Simulator - Admin Panel")

    # Placeholder for status messages
    status_placeholder = st.empty()

    # Sidebar for simulation trigger
    st.sidebar.header("🔄 Run Simulations")
    num_simulations = st.sidebar.number_input(
        "Number of Simulations", 
        min_value=10, 
        max_value=10000, 
        value=1000, 
        step=10
    )
    
    if st.sidebar.button("🚀 Run Simulation"):
        with st.spinner("🕒 Running simulations..."):
            try:
                summary = orchestrate_simulation_workflow(num_simulations)
                status_placeholder.success("✅ Simulations completed successfully!")
            except Exception as e:
                status_placeholder.error(f"❌ An error occurred during the simulation: {e}")
                logger.error(f"Simulation error: {e}")
                return

        if summary is not None:
            # Display total games
            st.subheader("📊 Total Games Simulated")
            st.write(summary.get('total_games', 'N/A'))
            logger.info("Displayed total games simulated.")
            
            # Load and execute all visualizations
            visualizations = load_visualizations()
            if not visualizations:
                st.warning("⚠️ No visualization modules found.")
                logger.warning("No visualization modules found.")
            else:
                # Create tabs for each visualization
                viz_tab_names = [viz.__name__.replace('_', ' ').title() for viz in visualizations]
                viz_tabs = st.tabs(viz_tab_names)
                for tab, viz in zip(viz_tabs, visualizations):
                    with tab:
                        try:
                            viz(summary)
                            logger.info(f"Executed visualization: {viz.__module__}")
                        except Exception as e:
                            st.error(f"❌ Error in visualization {viz.__module__}: {e}")
                            logger.error(f"Visualization {viz.__module__} error: {e}")
        
        # Provide download links for CSV files
        st.subheader("💾 Download Simulation Results")
        simulations = get_available_simulations(output_dir='data/simulations/')
        if simulations:
            # Dropdown to select simulation
            simulation_options = [sim['simulation_id'] for sim in simulations]
            selected_simulation_id = st.selectbox("Select a Simulation to View", simulation_options)
            
            # Find the selected simulation
            selected_sim = next((sim for sim in simulations if sim['simulation_id'] == selected_simulation_id), None)
            
            if selected_sim:
                st.write(f"**Simulation Details:** {selected_sim['simulation_id']}")
                st.write(f"**Last Run:** {selected_sim['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Arrange download buttons in columns
                st.markdown("### 📥 Download Files")
                cols = st.columns(len(selected_sim['files']))
                for col, (file_type, filepath) in zip(cols, selected_sim['files'].items()):
                    try:
                        df = pd.read_csv(filepath)
                        csv_buffer = convert_df_to_csv(df)
                        col.download_button(
                            label=f"Download {file_type.replace('_', ' ').title()}",
                            data=csv_buffer,
                            file_name=os.path.basename(filepath),
                            mime='text/csv'
                        )
                    except FileNotFoundError:
                        col.error(f"❌ {file_type.replace('_', ' ').title()} file not found.")
                        logger.error(f"{file_type} file not found at {filepath}")
                    except Exception as e:
                        col.error(f"❌ Failed to load {file_type.replace('_', ' ').title()}: {e}")
                        logger.error(f"Failed to load {filepath}: {e}")
                
                # Load and display visualizations for the selected simulation
                st.markdown("### 📈 Visualizations for Selected Simulation")
                # Reload the summary based on selected simulation's CSVs
                try:
                    team_scores_df = pd.read_csv(selected_sim['files']['team_scores'])
                    player_points_df = pd.read_csv(selected_sim['files']['player_points'])
                    player_percentiles_df = pd.read_csv(selected_sim['files']['player_percentiles'])
                    
                    # Create a new summary dictionary based on selected simulation
                    new_summary = {
                        'total_games': len(team_scores_df) // 2,  # Assuming two teams per game
                        'team_scores': {
                            team: team_scores_df[team_scores_df['team'] == team]['simulated_score'].tolist()
                            for team in team_scores_df['team'].unique()
                        },
                        'player_points': {
                            player: player_points_df[player_points_df['player_name'] == player]['projected_points'].tolist()
                            for player in player_points_df['player_name'].unique()
                        },
                        'player_percentiles': {
                            row['player_name']: row.drop('player_name').to_dict()
                            for _, row in player_percentiles_df.iterrows()
                        }
                    }

                    # Load and execute all visualizations with the new summary
                    visualizations = load_visualizations()
                    if not visualizations:
                        st.warning("⚠️ No visualization modules found.")
                        logger.warning("No visualization modules found.")
                    else:
                        # Create tabs for each visualization
                        viz_tab_names = [viz.__name__.replace('_', ' ').title() for viz in visualizations]
                        viz_tabs = st.tabs(viz_tab_names)
                        for tab, viz in zip(viz_tabs, visualizations):
                            with tab:
                                try:
                                    viz(new_summary)
                                    logger.info(f"Executed visualization: {viz.__module__}")
                                except Exception as e:
                                    st.error(f"❌ Error in visualization {viz.__module__}: {e}")
                                    logger.error(f"Visualization {viz.__module__} error: {e}")
                
                except Exception as e:
                    st.error(f"❌ Failed to load simulation data for visualizations: {e}")
                    logger.error(f"Failed to load simulation data for visualizations: {e}")
        else:
            st.info("ℹ️ No simulation CSV files found to download.")

if __name__ == "__main__":
    main()

