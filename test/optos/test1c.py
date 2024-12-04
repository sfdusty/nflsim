from datetime import datetime

import pandas as pd
from datetime import datetime

ROSTER_REQUIREMENTS = {
    "QB": 1,
    "RB": 2,
    "WR": 3,  # At least 3 WRs
    "TE": 1,
    "FLEX": 1,  # FLEX can be RB/WR/TE
    "DST": 1,
}




def preprocess_player_pool(player_pool):
    """
    Prepares the player pool with necessary columns for lineup optimization.

    Args:
        player_pool (pd.DataFrame): The raw player pool DataFrame.

    Returns:
        pd.DataFrame: Preprocessed player pool.
    """
    # Extract and parse game start time from the "Game Info" column
    def extract_game_time(game_info):
        try:
            return datetime.strptime(game_info.split(" ")[1] + " " + game_info.split(" ")[2], "%m/%d/%Y %I:%M%p")
        except:
            return None

    player_pool["GameTime"] = player_pool["Game Info"].apply(extract_game_time)

    # Add position eligibility flags
    player_pool["IsFLEX"] = player_pool[ "Position"].str.contains("RB|WR|TE")
    player_pool["IsWR"] = player_pool[ "Position"].str.contains("WR")
    player_pool["IsRB"] = player_pool[ "Position"].str.contains("RB")
    player_pool["IsTE"] = player_pool[ "Position"].str.contains("TE")
    player_pool["IsQB"] = player_pool[ "Position"].str.contains("QB")
    player_pool["IsDST"] = player_pool[ "Position"].str.contains("DST")

    return player_pool




def extract_game_time(game_info):
    """Extract and parse the game start time from the Game Info column."""
    try:
        return datetime.strptime(game_info.split(" ")[1] + " " + game_info.split(" ")[2], "%m/%d/%Y %I:%M%p")
    except:
        return None

def validate_player_pool(player_pool):
    """Ensure player pool contains required columns."""
    required_columns = { "Position", "Salary", "ProjPts", "Game Info"}
    missing = required_columns - set(player_pool.columns)
    if missing:
        raise ValueError(f"Missing required columns in player pool: {missing}")
        
        
def calibrate_variance(player_pool, diversity_level):
    """
    Calibrates variance levels for projection adjustments.

    Args:
        player_pool (pd.DataFrame): Player pool with projections.
        diversity_level (str): Diversity level ("low", "medium", "high").

    Returns:
        dict, float: Variance levels by position and team variance.
    """
    # Set base variance levels based on diversity level
    if diversity_level == "low":
        position_variance = {"QB": 0.02, "RB": 0.03, "WR": 0.05, "TE": 0.04, "DST": 0.01}
        team_variance = 0.02
    elif diversity_level == "medium":
        position_variance = {"QB": 0.05, "RB": 0.07, "WR": 0.1, "TE": 0.08, "DST": 0.03}
        team_variance = 0.05
    elif diversity_level == "high":
        position_variance = {"QB": 0.1, "RB": 0.15, "WR": 0.2, "TE": 0.15, "DST": 0.08}
        team_variance = 0.1
    else:
        raise ValueError("Invalid diversity level. Choose 'low', 'medium', or 'high'.")

    return position_variance, team_variance
        


def format_lineup_for_display(optimal_lineup):
    """
    Formats the optimized lineup for display, sorting by desired order, and adds total metrics.

    Args:
        optimal_lineup (pd.DataFrame): The optimized lineup.

    Returns:
        pd.DataFrame: Lineup sorted and formatted for display, including totals.
    """
    # Determine the Flex player based on the latest game start time
    flex_candidates = optimal_lineup[optimal_lineup["IsFLEX"]]
    flex_player = flex_candidates.loc[flex_candidates["GameTime"].idxmax()]

    # Exclude the Flex player and Defense temporarily for sorting
    non_flex_dst_lineup = optimal_lineup.loc[
        ~optimal_lineup.index.isin([flex_player.name]) & ~optimal_lineup["IsDST"]
    ].copy()

    # Sort the remaining lineup by position
    position_order = ["QB", "RB", "WR", "TE"]
    non_flex_dst_lineup["Order"] = non_flex_dst_lineup[ "Position"].apply(
        lambda pos: position_order.index(pos.split("/")[0]) if pos.split("/")[0] in position_order else 9
    )
    sorted_lineup = non_flex_dst_lineup.sort_values("Order")

    # Add Flex and Defense in the correct positions
    sorted_lineup = pd.concat(
        [
            sorted_lineup,
            flex_player.to_frame().T.assign(Order=7),  # Flex is second-to-last
            optimal_lineup[optimal_lineup["IsDST"]].assign(Order=8),  # Defense is last
        ],
        ignore_index=True,
    ).sort_values("Order")

    # Drop the temporary sorting column
    sorted_lineup = sorted_lineup.drop(columns="Order")

    # Calculate totals
    total_salary = sorted_lineup["Salary"].sum()
    total_proj_pts = sorted_lineup["ProjPts"].sum()
    total_proj_own = sorted_lineup["ProjOwn"].sum()

    # Create totals row
    totals_row = {
        "Name_x": "TOTALS",
        "TeamAbbrev": "",
         "Position": "",
        "Salary": total_salary,
        "ProjPts": total_proj_pts,
        "ProjOwn": total_proj_own,
        "GameTime": "",
    }

    # Add totals row to the lineup
    sorted_lineup = pd.concat([sorted_lineup, pd.DataFrame([totals_row])], ignore_index=True)

    # Return the final lineup
    return sorted_lineup[["Name", "TeamAbbrev",  "Position", "Salary", "ProjPts", "ProjOwn", "GameTime"]]

import pandas as pd
from collections import Counter

def calculate_player_exposures(lineups):
    """
    Calculates player exposures from a set of lineups.

    Args:
        lineups (list of pd.DataFrame): List of DataFrames, each representing a lineup.

    Returns:
        pd.DataFrame: A DataFrame listing players and their exposures, sorted by appearances.
    """
    # Flatten the player names from all lineups into a single list
    all_players = []
    for lineup in lineups:
        all_players.extend(lineup["Name"].tolist())  # Assuming "Name" is the player column

    # Count occurrences of each player
    player_counts = Counter(all_players)

    # Convert to a DataFrame
    exposures_df = pd.DataFrame(player_counts.items(), columns=["Player", "Appearances"])

    # Sort by appearances in descending order
    exposures_df = exposures_df.sort_values(by="Appearances", ascending=False).reset_index(drop=True)

    return exposures_df

def display_player_exposures(lineups):
    """
    Displays player exposures as a table.

    Args:
        lineups (list of pd.DataFrame): List of DataFrames, each representing a lineup.
    """
    exposures_df = calculate_player_exposures(lineups)
    print("\n=== Player Exposures ===")
    print(exposures_df)
    return exposures_df



import numpy as np

def generate_projection_sets(player_pool, num_sets=10, variance_range=0.1):
    """
    Generates multiple sets of adjusted projections with variance applied.

    Args:
        player_pool (pd.DataFrame): The player pool with projections.
        num_sets (int): Number of projection sets to generate.
        variance_range (float): Maximum percentage adjustment for variance (e.g., 0.1 for ±10%).

    Returns:
        list of pd.DataFrame: List of player pools with adjusted projections.
    """
    projection_sets = []

    for _ in range(num_sets):
        adjusted_player_pool = player_pool.copy()
        # Apply random variance to projections
        adjusted_player_pool["ProjPts"] = adjusted_player_pool["ProjPts"] * (
            1 + np.random.uniform(-variance_range, variance_range, len(player_pool))
        )
        projection_sets.append(adjusted_player_pool)

    return projection_sets


