# sim/utils/summarize_simulation_results.py

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def summarize_simulation_results(slate: dict) -> dict:
    """
    Summarizes the simulation results.

    Args:
        slate (dict): Dictionary containing simulated team scores and player points.

    Returns:
        dict: Summary including total games, player percentiles, and team scores.
    """
    logger.info("Summarizing simulation results...")
    total_games = len(next(iter(slate['team_scores'].values()), []))
    team_scores = slate['team_scores']
    player_points = slate.get('player_points', {})
    
    # Calculate player percentiles
    player_percentiles = {}
    for player, points in player_points.items():
        if points:
            player_percentiles[player] = {
                '25th': np.percentile(points, 25),
                '50th': np.percentile(points, 50),
                '75th': np.percentile(points, 75),
                '85th': np.percentile(points, 85),
                '95th': np.percentile(points, 95),
                '99th': np.percentile(points, 99)
            }
        else:
            logger.warning(f"No points data for player {player}. Skipping percentile calculation.")
    
    summary = {
        'total_games': total_games,
        'team_scores': team_scores,
        'player_points': player_points,
        'player_percentiles': player_percentiles
    }

    logger.info("Simulation results summarized.")
    return summary

