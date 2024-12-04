# modules/optimizer.py

from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpBinary, LpStatus

def optimize_lineup(lineup_data, salary_cap, roster_size=6):
    """
    Optimize DFS lineup based on projected fantasy points and salary cap.

    Args:
        lineup_data (pd.DataFrame): DataFrame containing player data with projected fantasy points.
            Expected columns: 'Name', 'salary', 'AverageFantasyPoints'
        salary_cap (int): Salary cap for the lineup.
        roster_size (int): Number of players to select for the lineup.

    Returns:
        pd.DataFrame: DataFrame of selected players for the lineup.
    """
    # Validate required columns
    required_columns = {'Name', 'salary', 'AverageFantasyPoints'}
    if not required_columns.issubset(lineup_data.columns):
        raise ValueError(f"lineup_data must contain columns: {required_columns}")

    # Create the LP problem
    prob = LpProblem("Lineup Optimization", LpMaximize)

    # Create decision variables
    player_vars = LpVariable.dicts("Player", lineup_data.index, cat=LpBinary)

    # Objective function: Maximize total projected fantasy points
    prob += lpSum([lineup_data.loc[i, 'AverageFantasyPoints'] * player_vars[i] for i in lineup_data.index])

    # Constraint: Total salary must be less than or equal to the salary cap
    prob += lpSum([lineup_data.loc[i, 'salary'] * player_vars[i] for i in lineup_data.index]) <= salary_cap

    # Constraint: Roster size (e.g., select 6 players)
    prob += lpSum([player_vars[i] for i in lineup_data.index]) == roster_size

    # Solve the problem
    prob.solve()

    # Log optimizer status
    logging.info(f"Optimizer Status: {LpStatus[prob.status]}")

    # Check if a valid solution was found
    if prob.status != 1:
        # No optimal solution found
        logging.warning("No optimal solution found for the lineup optimization.")
        return pd.DataFrame()

    # Get the selected players
    selected_indices = [i for i in lineup_data.index if player_vars[i].varValue == 1]
    selected_players = lineup_data.loc[selected_indices].reset_index(drop=True)

    return selected_players

