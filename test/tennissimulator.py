# modules/sim/simulator.py
# modules/sim/simconfig.py

import pandas as pd
from typing import Optional, Dict, Any, ClassVar, List
from dataclasses import dataclass
import logging

from utils.logger import SIM_LOG_MESSAGES, get_logger

# Initialize logger
sim_logger = get_logger('simulation')


@dataclass
class PlayerStats:
    """
    Dataclass representing a player's statistics using only rate (percentage-based) stats.
    """
    Player: str
    Surface: str
    League: str
    FirstServePercentage: float
    AcePercentage: float
    FirstServeWonPercentage: float
    SecondServeWonPercentage: float
    DoubleFaultPercentage: float
    ServiceGamesWonPercentage: float
    ReturnGamesWonPercentage: float
    PointsWonPercentage: float
    GamesWonPercentage: float
    SetsWonPercentage: float
    TieBreaksWonPercentage: float
    BreakPointsSavedPercentage: float
    BreakPointsConvertedPercentage: float
    FirstServeReturnPointsWonPercentage: float
    SecondServeReturnPointsWonPercentage: float
    ReturnPointsWonPercentage: float
    ServicePointsWonPercentage: float
    BreakPointsFacedPerServiceGame: float
    AceAgainstPercentage: float
    AcesAgainstPerReturnGame: float
    BreakPointChancesPerReturnGame: float

    # Class variable listing all required fields for validation
    REQUIRED_FIELDS: ClassVar[List[str]] = [
        'Player',
        'Surface',
        'League',
        'FirstServePercentage',
        'AcePercentage',
        'FirstServeWonPercentage',
        'SecondServeWonPercentage',
        'DoubleFaultPercentage',
        'ServiceGamesWonPercentage',
        'ReturnGamesWonPercentage',
        'PointsWonPercentage',
        'GamesWonPercentage',
        'SetsWonPercentage',
        'TieBreaksWonPercentage',
        'BreakPointsSavedPercentage',
        'BreakPointsConvertedPercentage',
        'FirstServeReturnPointsWonPercentage',
        'SecondServeReturnPointsWonPercentage',
        'ReturnPointsWonPercentage',
        'ServicePointsWonPercentage',
        'BreakPointsFacedPerServiceGame',
        'AceAgainstPercentage',
        'AcesAgainstPerReturnGame',
        'BreakPointChancesPerReturnGame'
    ]

    def __post_init__(self):
        """
        Validate that all required fields are present and within valid ranges.
        """
        for field_name in self.REQUIRED_FIELDS:
            value = getattr(self, field_name, None)
            if value is None:
                sim_logger.error(SIM_LOG_MESSAGES["missing_stat_warning"].format(
                    field=field_name,
                    player_name=self.Player
                ))
                raise ValueError(f"Missing required field: {field_name}")
            if isinstance(value, float) and not (0.0 <= value <= 1.0):
                sim_logger.error(SIM_LOG_MESSAGES["invalid_stat_value"].format(
                    field=field_name,
                    player_name=self.Player
                ))
                raise ValueError(f"Invalid value for {field_name}: {value}. Must be between 0 and 1.")

    def reset_match_stats(self):
        """
        Reset match-specific statistics to their default values before starting a new match.
        """
        pass  # No action needed as counts are handled in simulator.py


def load_player_data(filepath: str) -> pd.DataFrame:
    """
    Load player statistics from a CSV file, utilizing only rate (percentage-based) stats.

    Args:
        filepath (str): Path to the CSV file.

    Returns:
        pd.DataFrame: DataFrame containing player statistics.
    """
    try:
        player_data = pd.read_csv(filepath)
        player_data = player_data.copy()  # Work on a copy to avoid SettingWithCopyWarning

        # Ensure all required columns are present
        required_columns = [
            'Player',
            'Surface',
            'League',
            'FirstServePercentage',
            'AcePercentage',
            'FirstServeWonPercentage',
            'SecondServeWonPercentage',
            'DoubleFaultPercentage',
            'ServiceGamesWonPercentage',
            'ReturnGamesWonPercentage',
            'PointsWonPercentage',
            'GamesWonPercentage',
            'SetsWonPercentage',
            'TieBreaksWonPercentage',
            'BreakPointsSavedPercentage',
            'BreakPointsConvertedPercentage',
            'FirstServeReturnPointsWonPercentage',
            'SecondServeReturnPointsWonPercentage',
            'ReturnPointsWonPercentage',
            'ServicePointsWonPercentage',
            'BreakPointsFacedPerServiceGame',
            'AceAgainstPercentage',
            'AcesAgainstPerReturnGame',
            'BreakPointChancesPerReturnGame'
        ]
        missing_columns = [col for col in required_columns if col not in player_data.columns]
        if missing_columns:
            sim_logger.error(SIM_LOG_MESSAGES["missing_columns_error"].format(
                columns=', '.join(missing_columns)
            ))
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Standardize the 'Player' column to lowercase for case-insensitive matching
        player_data['Player_lower'] = player_data['Player'].str.lower()

        sim_logger.info(SIM_LOG_MESSAGES["load_player_data"].format(filepath=filepath))
        return player_data
    except Exception as e:
        # Corrected logging statement with both 'filepath' and 'error'
        sim_logger.error(SIM_LOG_MESSAGES["load_player_data_error"].format(filepath=filepath, error=e))
        return pd.DataFrame()


def get_player_stats(player_name: str, surface: str, player_data: pd.DataFrame) -> Optional[pd.Series]:
    """
    Retrieve player statistics based on name and surface.

    Args:
        player_name (str): Name of the player.
        surface (str): Surface type ('Hard', 'Clay', 'Grass', or 'All').
        player_data (pd.DataFrame): DataFrame containing player statistics.

    Returns:
        Optional[pd.Series]: Player statistics if found, else None.
    """
    player_name_lower = player_name.lower()
    surface_lower = surface.lower()

    # Filter based on the standardized 'Player_lower' name and 'Surface'
    player_row = player_data[
        (player_data['Player_lower'] == player_name_lower) &
        (player_data['Surface'].str.lower() == surface_lower)
    ]

    if player_row.empty:
        # Attempt to find stats with 'All' surfaces
        player_row = player_data[
            (player_data['Player_lower'] == player_name_lower) &
            (player_data['Surface'].str.lower() == 'all')
        ]

    if player_row.empty:
        sim_logger.warning(SIM_LOG_MESSAGES["get_player_stats_warning"].format(
            player_name=player_name, surface=surface
        ))
        return None

    return player_row.iloc[0]  # Return a single row as a Series


def calculate_fantasy_points(stats: Dict[str, Any], match_won: bool, best_of: int) -> float:
    """
    Calculate DraftKings fantasy points for a tennis player based on match statistics.

    Args:
        stats (Dict[str, Any]): Dictionary containing player's match statistics and bonuses.
            Expected keys:
                - 'MatchPlayed' (bool)
                - 'AdvancedByWalkover' (bool)
                - 'Aces' (int)
                - 'DoubleFaults' (int)
                - 'GamesWon' (int)
                - 'GamesLost' (int)
                - 'SetsWon' (int)
                - 'SetsLost' (int)
                - 'CleanSet' (bool)
                - 'StraightSets' (bool)
                - 'NoDoubleFault' (bool)
                - 'TenPlusAces' (bool)
                - 'FifteenPlusAces' (bool)
                - 'Breaks' (int)
        match_won (bool): Indicates whether the player won the match.
        best_of (int): Number of sets to play (3 or 5).

    Returns:
        float: Calculated fantasy points.
    """
    points = 0.0

    # Base Points
    if stats.get('MatchPlayed', False):
        points += 30  # Match Played

    if stats.get('AdvancedByWalkover', False):
        points += 30  # Advanced By Walkover

    # Match Outcome
    if match_won:
        if best_of == 3:
            points += 6  # Match Won for Best of 3
        elif best_of == 5:
            points += 5  # Match Won for Best of 5

    # Games
    games_won = stats.get('GamesWon', 0)
    games_lost = stats.get('GamesLost', 0)
    if best_of == 3:
        points += games_won * 2.5  # Game Won
        points -= games_lost * 2    # Game Lost
    elif best_of == 5:
        points += games_won * 2      # Game Won
        points -= games_lost * 1.6  # Game Lost

    # Sets
    sets_won = stats.get('SetsWon', 0)
    sets_lost = stats.get('SetsLost', 0)
    if best_of == 3:
        points += sets_won * 6    # Set Won
        points -= sets_lost * 3   # Set Lost
    elif best_of == 5:
        points += sets_won * 5    # Set Won
        points -= sets_lost * 2.5  # Set Lost

    # Aces
    aces = stats.get('Aces', 0)
    if best_of == 3:
        points += aces * 0.4  # Ace
    elif best_of == 5:
        points += aces * 0.25  # Ace

    # Double Faults
    double_faults = stats.get('DoubleFaults', 0)
    points -= double_faults * 1  # Double Fault

    # Breaks
    breaks = stats.get('Breaks', 0)
    if best_of == 3:
        points += breaks * 0.75  # Break
    elif best_of == 5:
        points += breaks * 0.5  # Break

    # Bonuses
    if stats.get('CleanSet', False):
        if best_of == 3:
            points += 4  # Clean Set Bonus for Best of 3
        elif best_of == 5:
            points += 2.5  # Clean Set Bonus for Best of 5

    if stats.get('StraightSets', False):
        if best_of == 3:
            points += 6  # Straight Sets Bonus for Best of 3
        elif best_of == 5:
            points += 5  # Straight Sets Bonus for Best of 5

    if stats.get('NoDoubleFault', False):
        if best_of == 3:
            points += 2.5  # No Double Fault Bonus for Best of 3
        elif best_of == 5:
            points += 5    # No Double Fault Bonus for Best of 5

    if stats.get('TenPlusAces', False):
        points += 2  # 10+ Ace Bonus

    if stats.get('FifteenPlusAces', False):
        points += 2  # 15+ Ace Bonus

    sim_logger.debug(f"Calculating fantasy points: {points} from stats: {stats}, Match Won: {match_won}, Best of: {best_of}")
    return points

import time
import numpy as np
from typing import Dict, Optional, List, Any
import logging
import pandas as pd  # Ensure pandas is imported

from modules.sim.simconfig import (
    PlayerStats,
    calculate_fantasy_points,
    get_player_stats,
    SIM_LOG_MESSAGES,
    sim_logger
)


def simulate_game(server_stats: PlayerStats, returner_stats: PlayerStats) -> Dict[str, Any]:
    """
    Simulate a single game in a tennis match, tracking relevant stats.

    Args:
        server_stats (PlayerStats): Statistics for the server (Player 1 or Player 2).
        returner_stats (PlayerStats): Statistics for the returner.

    Returns:
        Dict[str, Any]: Dictionary containing 'winner', 'aces', and 'double_faults'.
    """
    # Calculate probability of server winning the game
    # Adjusted to prevent one player from dominating
    server_effect = server_stats.FirstServeWonPercentage * server_stats.ServiceGamesWonPercentage
    returner_effect = returner_stats.ReturnPointsWonPercentage * returner_stats.GamesWonPercentage

    # Normalize probabilities to sum to 1
    total = server_effect + returner_effect
    if total == 0:
        server_win_prob = 0.5
        returner_win_prob = 0.5
    else:
        server_win_prob = server_effect / total
        returner_win_prob = returner_effect / total

    outcome = np.random.rand()
    winner = 'player1' if outcome < server_win_prob else 'player2'

    # Track Aces and Double Faults
    serves = 8  # Number of serves per game
    aces = np.random.binomial(serves, server_stats.AcePercentage)
    double_faults = np.random.binomial(serves, server_stats.DoubleFaultPercentage)

    sim_logger.debug(
        SIM_LOG_MESSAGES["game_result"].format(
            winner=winner,
            aces=aces,
            double_faults=double_faults
        )
    )
    return {
        'winner': winner,
        'aces': aces,
        'double_faults': double_faults
    }


def simulate_set(server_id: int, player1_stats: PlayerStats, player2_stats: PlayerStats) -> Dict[str, Any]:
    """
    Simulate a single set between two players, tracking game outcomes and counts.

    Args:
        server_id (int): ID of the serving player (1 or 2).
        player1_stats (PlayerStats): Statistics for Player 1.
        player2_stats (PlayerStats): Statistics for Player 2.

    Returns:
        Dict[str, Any]: Dictionary containing set winner, game outcomes, 'aces', and 'double_faults'.
    """
    player1_games = 0
    player2_games = 0
    games = []
    clean_set = True  # Assume clean set until a game is lost
    set_aces = 0
    set_double_faults = 0

    while True:
        if server_id == 1:
            game_result = simulate_game(player1_stats, player2_stats)
        else:
            game_result = simulate_game(player2_stats, player1_stats)

        winner = game_result['winner']
        aces = game_result['aces']
        double_faults = game_result['double_faults']

        set_aces += aces
        set_double_faults += double_faults

        games.append(winner)

        if winner == 'player1':
            player1_games += 1
        else:
            player2_games += 1
            clean_set = False  # Player lost a game in this set

        # Check for set win
        if (player1_games >= 6 or player2_games >= 6) and abs(player1_games - player2_games) >= 2:
            set_winner = 'player1' if player1_games > player2_games else 'player2'
            sim_logger.debug(f"Set Winner: {set_winner}, Games: {player1_games}-{player2_games}")
            return {
                'set_winner': set_winner,
                'games': games,
                'CleanSet': clean_set,
                'aces': set_aces,
                'double_faults': set_double_faults
            }

        # Tie-break condition
        if player1_games == 6 and player2_games == 6:
            tie_break_winner = simulate_tie_break(server_id, player1_stats, player2_stats)
            if tie_break_winner == 'player1':
                player1_games += 1
            else:
                player2_games += 1
            games.append(tie_break_winner)
            set_winner = 'player1' if player1_games > player2_games else 'player2'
            sim_logger.debug(f"Tie-Break Winner: {set_winner}, Games: {player1_games}-{player2_games}")
            return {
                'set_winner': set_winner,
                'games': games,
                'CleanSet': False,  # Tie-break implies the set wasn't clean
                'aces': set_aces,
                'double_faults': set_double_faults
            }

        # Alternate server
        server_id = 2 if server_id == 1 else 1


def simulate_tie_break(server_id: int, player1_stats: PlayerStats, player2_stats: PlayerStats) -> str:
    """
    Simulate a tie-break game in a tennis match.

    Args:
        server_id (int): ID of the serving player (1 or 2).
        player1_stats (PlayerStats): Statistics for Player 1.
        player2_stats (PlayerStats): Statistics for Player 2.

    Returns:
        str: 'player1' or 'player2' indicating the tie-break winner.
    """
    player1_points = 0
    player2_points = 0
    points_played = 0

    while True:
        points_played += 1
        # Determine current server based on tie-break rules
        if points_played == 1:
            current_server = server_id
        else:
            # After the first point, players alternate every two points
            current_server = 2 if ((points_played - 1) // 2) % 2 == 1 else 1

        # Simulate the point
        if current_server == 1:
            server_stats = player1_stats
            returner_stats = player2_stats
        else:
            server_stats = player2_stats
            returner_stats = player1_stats

        point_result = simulate_game(server_stats, returner_stats)
        point_winner = point_result['winner']
        # Aces and double faults in tie-breaks can be tracked if needed

        if point_winner == 'player1':
            player1_points += 1
        else:
            player2_points += 1

        sim_logger.debug(
            f"Tie-Break Point: {point_winner}, Current Score: Player1={player1_points}, Player2={player2_points}"
        )

        # Check for tie-break win condition
        if (player1_points >= 7 or player2_points >= 7) and abs(player1_points - player2_points) >= 2:
            tie_break_winner = 'player1' if player1_points > player2_points else 'player2'
            sim_logger.debug(f"Tie-Break Winner: {tie_break_winner}")
            return tie_break_winner


def simulate_match(player1_stats: PlayerStats, player2_stats: PlayerStats, best_of: int = 3) -> Dict[str, Any]:
    """
    Simulate a full tennis match between two players.

    Args:
        player1_stats (PlayerStats): Statistics for Player 1.
        player2_stats (PlayerStats): Statistics for Player 2.
        best_of (int, optional): Number of sets to play. Defaults to 3.

    Returns:
        Dict[str, Any]: Dictionary containing match winner, detailed set results, and fantasy points.
    """
    # Reset match-specific statistics before starting the match
    player1_stats.reset_match_stats()
    player2_stats.reset_match_stats()

    player1_sets = 0
    player2_sets = 0
    set_num = 1
    server_id = 1  # Assuming Player 1 serves first
    sets = []  # To store set-by-set outcomes

    # Initialize count-based statistics
    player1_fantasy_counts = {
        'Aces': 0,
        'DoubleFaults': 0,
        'GamesWon': 0,
        'GamesLost': 0,
        'SetsWon': 0,
        'SetsLost': 0,
        'Breaks': 0,
        'CleanSet': False,
        'StraightSets': False,
        'NoDoubleFault': True,
        'TenPlusAces': False,
        'FifteenPlusAces': False
    }

    player2_fantasy_counts = {
        'Aces': 0,
        'DoubleFaults': 0,
        'GamesWon': 0,
        'GamesLost': 0,
        'SetsWon': 0,
        'SetsLost': 0,
        'Breaks': 0,
        'CleanSet': False,
        'StraightSets': False,
        'NoDoubleFault': True,
        'TenPlusAces': False,
        'FifteenPlusAces': False
    }

    match_start_time = time.time()

    while True:
        set_result = simulate_set(server_id, player1_stats, player2_stats)
        set_winner = set_result['set_winner']
        games = set_result['games']
        clean_set = set_result['CleanSet']
        set_aces = set_result['aces']
        set_double_faults = set_result['double_faults']

        # Update set counts
        if set_winner == 'player1':
            player1_sets += 1
            player1_fantasy_counts['SetsWon'] += 1
            player2_fantasy_counts['SetsLost'] += 1
        else:
            player2_sets += 1
            player2_fantasy_counts['SetsWon'] += 1
            player1_fantasy_counts['SetsLost'] += 1

        # Update game counts
        player1_fantasy_counts['GamesWon'] += games.count('player1')
        player1_fantasy_counts['GamesLost'] += games.count('player2')
        player2_fantasy_counts['GamesWon'] += games.count('player2')
        player2_fantasy_counts['GamesLost'] += games.count('player1')

        # Update break points
        # For simplicity, assume each break is one break point converted
        player1_fantasy_counts['Breaks'] += games.count('player1')
        player2_fantasy_counts['Breaks'] += games.count('player2')

        # Update Aces and Double Faults
        player1_fantasy_counts['Aces'] += set_aces if set_winner == 'player1' else 0
        player1_fantasy_counts['DoubleFaults'] += set_double_faults if set_winner == 'player1' else 0
        player2_fantasy_counts['Aces'] += set_aces if set_winner == 'player2' else 0
        player2_fantasy_counts['DoubleFaults'] += set_double_faults if set_winner == 'player2' else 0

        # Update No Double Fault Bonus
        if (set_winner == 'player1' and set_double_faults > 0) or \
           (set_winner == 'player2' and set_double_faults > 0):
            if set_winner == 'player1':
                player1_fantasy_counts['NoDoubleFault'] = False
            else:
                player2_fantasy_counts['NoDoubleFault'] = False

        # Update TenPlusAces and FifteenPlusAces Bonuses
        if player1_fantasy_counts['Aces'] >= 15:
            player1_fantasy_counts['FifteenPlusAces'] = True
        elif player1_fantasy_counts['Aces'] >= 10:
            player1_fantasy_counts['TenPlusAces'] = True

        if player2_fantasy_counts['Aces'] >= 15:
            player2_fantasy_counts['FifteenPlusAces'] = True
        elif player2_fantasy_counts['Aces'] >= 10:
            player2_fantasy_counts['TenPlusAces'] = True

        # Update Clean Set Bonus
        if clean_set:
            if set_winner == 'player1':
                player1_fantasy_counts['CleanSet'] = True
            else:
                player2_fantasy_counts['CleanSet'] = True

        sets.append({
            'set_number': set_num,
            'winner': set_winner,
            'games': games,
            'CleanSet': clean_set
        })

        sim_logger.debug(f"Set {set_num} Winner: {set_winner}, Score: Player1={player1_sets}-Player2={player2_sets}")

        # Check for match winner
        required_sets = (best_of // 2) + 1
        if player1_sets == required_sets or player2_sets == required_sets:
            match_winner = 'player1' if player1_sets > player2_sets else 'player2'
            match_duration = time.time() - match_start_time

            # Determine Straight Sets Bonus
            straight_sets = (player1_sets == required_sets and player2_sets == 0) or \
                            (player2_sets == required_sets and player1_sets == 0)
            if straight_sets:
                if match_winner == 'player1':
                    player1_fantasy_counts['StraightSets'] = True
                else:
                    player2_fantasy_counts['StraightSets'] = True

            # Prepare stats for fantasy points calculation for both players
            fantasy_stats_player1 = {
                'MatchPlayed': True,
                'AdvancedByWalkover': False,
                'Aces': player1_fantasy_counts['Aces'],
                'DoubleFaults': player1_fantasy_counts['DoubleFaults'],
                'GamesWon': player1_fantasy_counts['GamesWon'],
                'GamesLost': player1_fantasy_counts['GamesLost'],
                'SetsWon': player1_fantasy_counts['SetsWon'],
                'SetsLost': player1_fantasy_counts['SetsLost'],
                'CleanSet': player1_fantasy_counts['CleanSet'],
                'StraightSets': player1_fantasy_counts['StraightSets'],
                'NoDoubleFault': player1_fantasy_counts['NoDoubleFault'],
                'TenPlusAces': player1_fantasy_counts['TenPlusAces'],
                'FifteenPlusAces': player1_fantasy_counts['FifteenPlusAces'],
                'Breaks': player1_fantasy_counts['Breaks']
            }

            fantasy_stats_player2 = {
                'MatchPlayed': True,
                'AdvancedByWalkover': False,
                'Aces': player2_fantasy_counts['Aces'],
                'DoubleFaults': player2_fantasy_counts['DoubleFaults'],
                'GamesWon': player2_fantasy_counts['GamesWon'],
                'GamesLost': player2_fantasy_counts['GamesLost'],
                'SetsWon': player2_fantasy_counts['SetsWon'],
                'SetsLost': player2_fantasy_counts['SetsLost'],
                'CleanSet': player2_fantasy_counts['CleanSet'],
                'StraightSets': player2_fantasy_counts['StraightSets'],
                'NoDoubleFault': player2_fantasy_counts['NoDoubleFault'],
                'TenPlusAces': player2_fantasy_counts['TenPlusAces'],
                'FifteenPlusAces': player2_fantasy_counts['FifteenPlusAces'],
                'Breaks': player2_fantasy_counts['Breaks']
            }

            # Calculate Fantasy Points
            player1_fantasy_points = calculate_fantasy_points(
                stats=fantasy_stats_player1,
                match_won=(match_winner == 'player1'),
                best_of=best_of
            )

            player2_fantasy_points = calculate_fantasy_points(
                stats=fantasy_stats_player2,
                match_won=(match_winner == 'player2'),
                best_of=best_of
            )

            # Return match results with separate fantasy points
            return {
                'winner': match_winner,
                'sets': sets,
                'player1_fantasy_points': player1_fantasy_points,
                'player2_fantasy_points': player2_fantasy_points,
                'duration': match_duration
            }

        set_num += 1
        server_id = 2 if server_id == 1 else 1


def run_match_simulation(player1_name: str, player2_name: str, surface: str, player_data: pd.DataFrame,
                        best_of: int = 3) -> Optional[Dict[str, Any]]:
    """
    Run a single match simulation between two players.

    Args:
        player1_name (str): Name of Player 1.
        player2_name (str): Name of Player 2.
        surface (str): Surface type ('Hard', 'Clay', 'Grass', 'All').
        player_data (pd.DataFrame): DataFrame containing player statistics.
        best_of (int, optional): Number of sets to play. Defaults to 3.

    Returns:
        Optional[Dict[str, Any]]: Dictionary containing match winner, detailed set results, and fantasy points.
    """
    try:
        player1_stats_row = get_player_stats(player1_name, surface, player_data)
        player2_stats_row = get_player_stats(player2_name, surface, player_data)

        if player1_stats_row is None or player2_stats_row is None:
            missing_player = 'Player 1' if player1_stats_row is None else 'Player 2'
            sim_logger.error(SIM_LOG_MESSAGES["error_running_match_simulation"].format(
                error=f"Player data not found for {missing_player}."
            ))
            return None
    except ValueError as ve:
        sim_logger.error(SIM_LOG_MESSAGES["error_running_match_simulation"].format(error=str(ve)))
        return None

    # Extract relevant statistics based on PlayerStats annotations
    player1_stats_data = {k: v for k, v in player1_stats_row.to_dict().items() if k in PlayerStats.REQUIRED_FIELDS}
    player2_stats_data = {k: v for k, v in player2_stats_row.to_dict().items() if k in PlayerStats.REQUIRED_FIELDS}

    try:
        player1_stats = PlayerStats(**player1_stats_data)
        player2_stats = PlayerStats(**player2_stats_data)
        sim_logger.info(SIM_LOG_MESSAGES["dataclass_initialized"])
    except ValueError as ve:
        sim_logger.error(SIM_LOG_MESSAGES["error_running_match_simulation"].format(error=str(ve)))
        return None

    try:
        match_result = simulate_match(player1_stats, player2_stats, best_of)
        return match_result
    except Exception as e:
        sim_logger.error(SIM_LOG_MESSAGES["error_running_match_simulation"].format(error=str(e)))
        return None

