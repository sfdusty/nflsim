# sim/utils/save_simulation_results_to_csv.py

import pandas as pd
import logging
import os
from datetime import datetime
import re
from .move_old_simulation_files import move_old_simulation_files
from .summarize_simulation_results import summarize_simulation_results

logger = logging.getLogger(__name__)

def sanitize_team_name(team_name: str) -> str:
    """
    Sanitizes team names to be filesystem-friendly by replacing spaces and removing special characters.
    
    Args:
        team_name (str): The team name to sanitize.
    
    Returns:
        str: Sanitized team name.
    """
    # Replace spaces with underscores
    sanitized = team_name.replace(' ', '_')
    # Remove any character that is not alphanumeric or underscore
    sanitized = re.sub(r'[^\w]', '', sanitized)
    return sanitized

def save_simulation_results_to_csv(summary: dict, game_metadata: dict, output_dir: str = 'data/simulations/'):
    """
    Saves simulation results to CSV files with full team names in filenames and moves old files to backup.

    Args:
        summary (dict): Summary of simulation results.
        game_metadata (dict): Metadata about the game.
        output_dir (str): Directory to save the CSV files.
    """
    logger.info("Saving simulation results to CSV files...")

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Move old simulation files to backup before saving new ones
    move_old_simulation_files(simulation_dir=output_dir, backup_dir=os.path.join(output_dir, 'backup/'))

    # Generate a timestamp for unique file naming
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    game_id = game_metadata.get('game_id', 'unknown_game')

    team1_full = game_metadata.get('team1_name', 'Team1')
    team2_full = game_metadata.get('team2_name', 'Team2')

    team1_sanitized = sanitize_team_name(team1_full)
    team2_sanitized = sanitize_team_name(team2_full)

    # File paths with full team names
    team_scores_file = os.path.join(output_dir, f'team_scores_{team1_sanitized}_{team2_sanitized}_{timestamp}.csv')
    player_points_file = os.path.join(output_dir, f'player_points_{team1_sanitized}_{team2_sanitized}_{timestamp}.csv')
    player_percentiles_file = os.path.join(output_dir, f'player_percentiles_{team1_sanitized}_{team2_sanitized}_{timestamp}.csv')

    # Save team scores
    team_scores_records = []
    for team, scores in summary['team_scores'].items():
        for score in scores:
            team_scores_records.append({
                'team': team,
                'simulated_score': score
            })
    team_scores_df = pd.DataFrame(team_scores_records)
    team_scores_df.to_csv(team_scores_file, index=False)
    logger.info(f"Team scores saved to {team_scores_file}")

    # Save player points
    player_points_records = []
    for player, points in summary['player_points'].items():
        for sim_id, point in enumerate(points, start=1):
            player_points_records.append({
                'simulation_id': sim_id,
                'player_name': player,
                'projected_points': point
            })
    player_points_df = pd.DataFrame(player_points_records)
    player_points_df.to_csv(player_points_file, index=False)
    logger.info(f"Player points saved to {player_points_file}")

    # Save player percentiles
    if summary.get('player_percentiles'):
        player_percentiles_records = []
        for player, percentiles in summary['player_percentiles'].items():
            record = {'player_name': player}
            record.update(percentiles)
            player_percentiles_records.append(record)
        player_percentiles_df = pd.DataFrame(player_percentiles_records)
        player_percentiles_df.to_csv(player_percentiles_file, index=False)
        logger.info(f"Player percentiles saved to {player_percentiles_file}")
    else:
        logger.warning("No player percentiles to save.")

    logger.info("All simulation results have been saved successfully.")

