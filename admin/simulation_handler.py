# admin/simulation_handler.py

import pandas as pd
import logging
from datetime import datetime
from sim.utils.summarize_simulation_results import summarize_simulation_results
from sim.utils.save_simulation_results_to_csv import save_simulation_results_to_csv
from utils.file_handler.read_and_process_raw_csvs import read_and_process_raw_csvs
from sim.simulator import run_simulation_slate

logger = logging.getLogger(__name__)

def orchestrate_simulation_workflow(num_simulations: int = 100, 
                                    raw_data_dir: str = 'data/raw/', 
                                    projection_path: str = 'data/projections/default/') -> dict:
    """
    Orchestrates the simulation workflow: loading raw data, running simulations with projections,
    summarizing results, and saving to CSV.

    Args:
        num_simulations (int): The number of simulations to run.
        raw_data_dir (str): Path to the raw data CSV files.
        projection_path (str): Path to the projection CSV files.

    Returns:
        dict: Summary of simulation results.

    Raises:
        FileNotFoundError: If the processed data or game metadata is not loaded correctly.
    """
    logger.info("[Step 1] Loading and processing raw data...")
    try:
        processed_data, game_metadata = read_and_process_raw_csvs(raw_data_dir=raw_data_dir)
    except Exception as e:
        logger.error(f"Error loading and processing raw data: {e}")
        raise

    # Updated condition to check if DataFrame is empty
    if processed_data.empty or not game_metadata:
        logger.error("Processed data is empty or game metadata is None. Ensure raw files are present and correctly formatted.")
        raise FileNotFoundError("Processed data is empty or game metadata is None.")

    # Ensure team names are present
    if 'team1_name' not in game_metadata or 'team2_name' not in game_metadata:
        logger.error("Game metadata must include 'team1_name' and 'team2_name'.")
        raise KeyError("Game metadata must include 'team1_name' and 'team2_name'.")

    logger.info("[Step 2] Running simulations...")
    try:
        slate = run_simulation_slate(processed_data, game_metadata, num_simulations, projection_path=projection_path)
    except Exception as e:
        logger.error(f"Error during simulation: {e}")
        raise

    logger.info("[Step 3] Summarizing results...")
    try:
        summary = summarize_simulation_results(slate)
    except Exception as e:
        logger.error(f"Error during summarization: {e}")
        raise

    logger.info("[Step 4] Saving simulation results to CSV...")
    try:
        save_simulation_results_to_csv(summary, game_metadata, output_dir='data/simulations/')
    except Exception as e:
        logger.error(f"Error during saving to CSV: {e}")
        raise

    logger.info("[Workflow Complete] Simulation, summarization, and saving completed successfully.")
    return summary

def get_available_simulations(output_dir: str = 'data/simulations/') -> list:
    """
    Retrieves a list of available simulation identifiers based on CSV filenames.

    Args:
        output_dir (str): Directory where simulation CSV files are stored.

    Returns:
        list: List of available simulation identifiers.
    """
    import glob
    import os
    import re

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

def load_simulation_summary(simulation: dict) -> dict:
    """
    Loads simulation data from CSV files and constructs a summary dictionary.

    Args:
        simulation (dict): Simulation details including file paths.

    Returns:
        dict: Summary of simulation results.
    """
    try:
        team_scores_df = pd.read_csv(simulation['files']['team_scores'])
        player_points_df = pd.read_csv(simulation['files']['player_points'])
        player_percentiles_df = pd.read_csv(simulation['files']['player_percentiles'])
        
        summary = {
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
        logger.info(f"Loaded simulation summary for {simulation['simulation_id']}")
        return summary
    except Exception as e:
        logger.error(f"Failed to load simulation summary: {e}")
        raise
