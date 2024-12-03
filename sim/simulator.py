# sim/simulator.py
import pandas as pd
import logging
from sim.models import Team
import numpy as np

logger = logging.getLogger(__name__)

def run_simulation_slate(processed_data: pd.DataFrame, game_metadata: dict, num_simulations: int) -> dict:
    """
    Runs the simulation slate for both teams and simulates player points.
    
    Args:
        processed_data (pd.DataFrame): Processed player data.
        game_metadata (dict): Metadata about the game, including team names and totals.
        num_simulations (int): Number of simulations to run.
    
    Returns:
        dict: Simulation results including simulated team scores and player points.
    """
    logger.info("Starting simulation slate...")
    team1 = Team(name=game_metadata['team1_name'], implied_total=game_metadata['team1_total'])
    team2 = Team(name=game_metadata['team2_name'], implied_total=game_metadata['team2_total'])

    # Add players to teams
    for player in game_metadata['team1_players']:
        team1.players.append(player)
    for player in game_metadata['team2_players']:
        team2.players.append(player)
    
    # Simulate team scores
    team1.simulate_scores(num_simulations)
    team2.simulate_scores(num_simulations)

    # Collect simulated team scores
    simulated_scores = {
        team1.name: team1.simulated_scores.tolist(),
        team2.name: team2.simulated_scores.tolist()
    }

    logger.info("Simulating player points...")
    player_points = {}
    
    # Simulate player points for team1
    for player in team1.players:
        # Simulate player points based on base and std_dev
        simulated_player_points = np.random.normal(
            loc=player['base'],
            scale=player['std_dev'],
            size=num_simulations
        )
        # Optionally, adjust points based on team_share
        simulated_player_points = simulated_player_points * player.get('team_share', 1)
        player_points[player['name']] = simulated_player_points.tolist()
        logger.debug(f"Simulated points for player {player['name']}: {simulated_player_points[:5]}")

    # Simulate player points for team2
    for player in team2.players:
        simulated_player_points = np.random.normal(
            loc=player['base'],
            scale=player['std_dev'],
            size=num_simulations
        )
        simulated_player_points = simulated_player_points * player.get('team_share', 1)
        player_points[player['name']] = simulated_player_points.tolist()
        logger.debug(f"Simulated points for player {player['name']}: {simulated_player_points[:5]}")

    logger.info("Simulation slate completed successfully.")
    return {
        'team_scores': simulated_scores,
        'player_points': player_points
    }

