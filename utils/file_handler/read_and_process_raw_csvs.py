import os
import pandas as pd
import numpy as np
from utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, FULL_MERGED_FILE, SLIMMED_PROJECTIONS_FILE
import logging

logger = logging.getLogger(__name__)

def handle() -> tuple:
    """
    Reads raw CSV files, processes them, and returns the processed DataFrame and game metadata.

    Returns:
        tuple: (processed_df, game_metadata)
    """
    try:
        logger.info("[Step 1] Fetching CSV files...")
        csv_files = get_csv_files(RAW_DATA_DIR)
        logger.info(f"CSV files found: {csv_files}")
        
        logger.info("[Step 2] Identifying CSV files...")
        ftn_df, saber_df = identify_csv_files(csv_files)
        
        logger.info("[Step 3] Adding 'Role' column to FTN data...")
        if ftn_df is not None:
            ftn_df = add_role_column(ftn_df)
        else:
            logger.warning("No FTN DataFrame found. Skipping 'Role' column addition.")
        
        logger.info("[Step 4] Merging CSV files...")
        merged_df = merge_csv_files(ftn_df, saber_df)
        
        logger.info("[Step 5] Processing merged data...")
        processed_df, game_metadata = process_merged_data(merged_df)
        
        logger.info("[Step 6] Saving processed files...")
        save_processed_files(processed_df)  # Save processed data to disk
        
        return processed_df, game_metadata
    except Exception as e:
        logger.error(f"Error in file handling: {e}")
        return None, None

def get_csv_files(directory: str) -> list:
    """Fetch all CSV files in the specified directory."""
    csv_files = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.csv')]
    if not csv_files:
        logger.error(f"No CSV files found in the directory: {directory}")
        raise FileNotFoundError(f"No CSV files found in the directory: {directory}")
    return csv_files

def identify_csv_files(csv_files: list) -> tuple:
    """
    Identify the FTN and SaberSim files from the list of CSV files based on column count.

    Args:
        csv_files (list): List of CSV file paths.

    Returns:
        tuple: (ftn_df, saber_df)
    """
    ftn_df, saber_df = None, None
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            num_columns = len(df.columns)

            if num_columns == 6:  # FTN file has 6 columns
                ftn_df = df
                logger.info(f"FTN file detected: {file}")
            elif num_columns > 40:  # SaberSim file has many columns
                saber_df = df
                logger.info(f"SaberSim file detected: {file}")
            else:
                logger.warning(f"Skipping unrecognized file: {file}")
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")
    return ftn_df, saber_df

def add_role_column(ftn_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'Role' column to the FTN DataFrame based on the 'Id' column.

    Args:
        ftn_df (pd.DataFrame): FTN DataFrame.

    Returns:
        pd.DataFrame: FTN DataFrame with the 'Role' column added.
    """
    if 'Id' in ftn_df.columns:
        ftn_df[['Id', 'Role']] = ftn_df['Id'].str.split('|', expand=True)
        logger.info("Added 'Role' column to FTN data.")
    else:
        logger.error("The 'Id' column is missing in the FTN data. Cannot add 'Role' column.")
        raise KeyError("The 'Id' column is missing in the FTN data. Cannot add 'Role' column.")
    return ftn_df

def merge_csv_files(ftn_df: pd.DataFrame, saber_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge the FTN and SaberSim data based on the player ID.

    Args:
        ftn_df (pd.DataFrame): FTN DataFrame.
        saber_df (pd.DataFrame): SaberSim DataFrame.

    Returns:
        pd.DataFrame: Merged DataFrame.
    """
    if ftn_df is None and saber_df is None:
        logger.error("No valid FTN or SaberSim files found.")
        raise FileNotFoundError("No valid FTN or SaberSim files found.")

    if ftn_df is not None and saber_df is not None:
        ftn_df['Id'] = ftn_df['Id'].astype(str)
        saber_df['DFS ID'] = saber_df['DFS ID'].astype(str)
        merged_df = pd.merge(
            ftn_df,
            saber_df,
            how="left",
            left_on="Id",
            right_on="DFS ID"
        )
        logger.info("Merged FTN and SaberSim data successfully.")
    else:
        merged_df = ftn_df or saber_df
        logger.warning("Only one of FTN or SaberSim data is available. Proceeding with available data.")

    return merged_df

def process_merged_data(merged_df: pd.DataFrame) -> tuple:
    """
    Processes the merged DataFrame by adding calculated columns and assigning teams.

    Args:
        merged_df (pd.DataFrame): Merged DataFrame.

    Returns:
        tuple: (filtered_df, game_metadata)
    """
    # Calculate base points and estimated std dev
    merged_df['base'] = merged_df[['ProjPts', 'My Proj']].mean(axis=1, skipna=True)
    merged_df['estimated_std_dev'] = 1.97 * merged_df['base'] ** 0.501
    logger.info("Calculated 'base' and 'estimated_std_dev' columns.")

    # Extract unique team totals
    team_totals = merged_df[['Team_x', 'Saber Team']].drop_duplicates(subset=['Team_x'])
    
    # Assign team names and totals
    unique_teams = team_totals['Team_x'].unique()
    if len(unique_teams) == 2:
        team1, team2 = unique_teams[0], unique_teams[1]
        team1_total = team_totals[team_totals['Team_x'] == team1]['Saber Team'].values[0]
        team2_total = team_totals[team_totals['Team_x'] == team2]['Saber Team'].values[0]
        logger.info(f"Teams Identified: {team1}, {team2}")
        logger.info(f"Team Totals - {team1}: {team1_total}, {team2}: {team2_total}")
    else:
        logger.error(f"Expected exactly 2 teams, found {len(unique_teams)}: {unique_teams}")
        raise ValueError(f"Expected exactly 2 teams, found {len(unique_teams)}: {unique_teams}")

    # Assign team_designation
    merged_df['team_designation'] = merged_df['Team_x'].apply(
        lambda x: 'team1' if x == team1 else 'team2'
    )
    logger.info("Assigned 'team_designation' to players.")

    # Calculate team share per player
    team_totals_df = merged_df.groupby('Team_x')['base'].transform('sum')
    merged_df['team_share'] = merged_df['base'] / team_totals_df
    logger.info("Calculated 'team_share' for each player.")

    # Filter players with base > 0
    filtered_df = merged_df[merged_df['base'] > 0].copy()
    logger.info(f"{len(filtered_df)} players retained after filtering.")

    # Generate game metadata
    game_metadata = {
        'team1_name': team1,
        'team1_total': team1_total,
        'team2_name': team2,
        'team2_total': team2_total,
        'team1_players': filtered_df[filtered_df['team_designation'] == 'team1'][[
            'Name_x', 'Position', 'base', 'estimated_std_dev'
        ]].rename(columns={
            'Name_x': 'name', 
            'Position': 'position', 
            'base': 'base', 
            'estimated_std_dev': 'std_dev'
        }).to_dict(orient='records'),
        'team2_players': filtered_df[filtered_df['team_designation'] == 'team2'][[
            'Name_x', 'Position', 'base', 'estimated_std_dev'
        ]].rename(columns={
            'Name_x': 'name', 
            'Position': 'position', 
            'base': 'base', 
            'estimated_std_dev': 'std_dev'
        }).to_dict(orient='records'),
    }

    logger.info(f"Assigned teams: {team1} -> team1, {team2} -> team2")
    logger.info(f"Generated game metadata.")

    return filtered_df, game_metadata

def save_processed_files(processed_df: pd.DataFrame) -> None:
    """
    Save the processed data to full and slimmed-down CSV files.

    Args:
        processed_df (pd.DataFrame): Processed DataFrame.
    """
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    logger.info(f"Ensured that processed data directory exists: {PROCESSED_DATA_DIR}")

    # Save the full merged file
    processed_df.to_csv(FULL_MERGED_FILE, index=False)
    logger.info(f"Merged file saved to: {FULL_MERGED_FILE}")

    # Save the slimmed-down file
    slimmed_df = processed_df[['Id', 'Name_x', 'Role', 'Position', 'Team_x', 'Opp', 'base', 
                               'estimated_std_dev', 'team_share', 'Saber Team']].copy()
    slimmed_df.rename(columns={
        'Name_x': 'name',
        'Team_x': 'team',
        'Saber Team': 'implied_team_total'
    }, inplace=True)

    slimmed_output_file = SLIMMED_PROJECTIONS_FILE
    slimmed_df.to_csv(slimmed_output_file, index=False)
    logger.info(f"Slimmed file saved to: {slimmed_output_file}")

def get_csv_files(directory: str) -> list:
    """Fetch all CSV files in the specified directory."""
    csv_files = [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.csv')]
    if not csv_files:
        logger.error(f"No CSV files found in the directory: {directory}")
        raise FileNotFoundError(f"No CSV files found in the directory: {directory}")
    return csv_files

def identify_csv_files(csv_files: list) -> tuple:
    """
    Identify the FTN and SaberSim files from the list of CSV files based on column count.

    Args:
        csv_files (list): List of CSV file paths.

    Returns:
        tuple: (ftn_df, saber_df)
    """
    ftn_df, saber_df = None, None
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            num_columns = len(df.columns)

            if num_columns == 6:  # FTN file has 6 columns
                ftn_df = df
                logger.info(f"FTN file detected: {file}")
            elif num_columns > 40:  # SaberSim file has many columns
                saber_df = df
                logger.info(f"SaberSim file detected: {file}")
            else:
                logger.warning(f"Skipping unrecognized file: {file}")
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")
    return ftn_df, saber_df

def add_role_column(ftn_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'Role' column to the FTN DataFrame based on the 'Id' column.

    Args:
        ftn_df (pd.DataFrame): FTN DataFrame.

    Returns:
        pd.DataFrame: FTN DataFrame with the 'Role' column added.
    """
    if 'Id' in ftn_df.columns:
        ftn_df[['Id', 'Role']] = ftn_df['Id'].str.split('|', expand=True)
        logger.info("Added 'Role' column to FTN data.")
    else:
        logger.error("The 'Id' column is missing in the FTN data. Cannot add 'Role' column.")
        raise KeyError("The 'Id' column is missing in the FTN data. Cannot add 'Role' column.")
    return ftn_df

def merge_csv_files(ftn_df: pd.DataFrame, saber_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge the FTN and SaberSim data based on the player ID.

    Args:
        ftn_df (pd.DataFrame): FTN DataFrame.
        saber_df (pd.DataFrame): SaberSim DataFrame.

    Returns:
        pd.DataFrame: Merged DataFrame.
    """
    if ftn_df is None and saber_df is None:
        logger.error("No valid FTN or SaberSim files found.")
        raise FileNotFoundError("No valid FTN or SaberSim files found.")

    if ftn_df is not None and saber_df is not None:
        ftn_df['Id'] = ftn_df['Id'].astype(str)
        saber_df['DFS ID'] = saber_df['DFS ID'].astype(str)
        merged_df = pd.merge(
            ftn_df,
            saber_df,
            how="left",
            left_on="Id",
            right_on="DFS ID"
        )
        logger.info("Merged FTN and SaberSim data successfully.")
    else:
        merged_df = ftn_df or saber_df
        logger.warning("Only one of FTN or SaberSim data is available. Proceeding with available data.")

    return merged_df

def process_merged_data(merged_df: pd.DataFrame) -> tuple:
    """
    Processes the merged DataFrame by adding calculated columns and assigning teams.

    Args:
        merged_df (pd.DataFrame): Merged DataFrame.

    Returns:
        tuple: (filtered_df, game_metadata)
    """
    # Calculate base points and estimated std dev
    merged_df['base'] = merged_df[['ProjPts', 'My Proj']].mean(axis=1, skipna=True)
    merged_df['estimated_std_dev'] = 1.97 * merged_df['base'] ** 0.501
    logger.info("Calculated 'base' and 'estimated_std_dev' columns.")

    # Extract unique team totals
    team_totals = merged_df[['Team_x', 'Saber Team']].drop_duplicates(subset=['Team_x'])
    
    # Assign team names and totals
    unique_teams = team_totals['Team_x'].unique()
    if len(unique_teams) == 2:
        team1, team2 = unique_teams[0], unique_teams[1]
        team1_total = team_totals[team_totals['Team_x'] == team1]['Saber Team'].values[0]
        team2_total = team_totals[team_totals['Team_x'] == team2]['Saber Team'].values[0]
        logger.info(f"Teams Identified: {team1}, {team2}")
        logger.info(f"Team Totals - {team1}: {team1_total}, {team2}: {team2_total}")
    else:
        logger.error(f"Expected exactly 2 teams, found {len(unique_teams)}: {unique_teams}")
        raise ValueError(f"Expected exactly 2 teams, found {len(unique_teams)}: {unique_teams}")

    # Assign team_designation
    merged_df['team_designation'] = merged_df['Team_x'].apply(
        lambda x: 'team1' if x == team1 else 'team2'
    )
    logger.info("Assigned 'team_designation' to players.")

    # Calculate team share per player
    team_totals_df = merged_df.groupby('Team_x')['base'].transform('sum')
    merged_df['team_share'] = merged_df['base'] / team_totals_df
    logger.info("Calculated 'team_share' for each player.")

    # Filter players with base > 0
    filtered_df = merged_df[merged_df['base'] > 0].copy()
    logger.info(f"{len(filtered_df)} players retained after filtering.")

    # Generate game metadata
    game_metadata = {
        'team1_name': team1,
        'team1_total': team1_total,
        'team2_name': team2,
        'team2_total': team2_total,
        'team1_players': filtered_df[filtered_df['team_designation'] == 'team1'][[
            'Name_x', 'Position', 'base', 'estimated_std_dev'
        ]].rename(columns={
            'Name_x': 'name', 
            'Position': 'position', 
            'base': 'base', 
            'estimated_std_dev': 'std_dev'
        }).to_dict(orient='records'),
        'team2_players': filtered_df[filtered_df['team_designation'] == 'team2'][[
            'Name_x', 'Position', 'base', 'estimated_std_dev'
        ]].rename(columns={
            'Name_x': 'name', 
            'Position': 'position', 
            'base': 'base', 
            'estimated_std_dev': 'std_dev'
        }).to_dict(orient='records'),
    }

    logger.info(f"Assigned teams: {team1} -> team1, {team2} -> team2")
    logger.info(f"Generated game metadata.")

    return filtered_df, game_metadata

def save_processed_files(processed_df: pd.DataFrame) -> None:
    """
    Save the processed data to full and slimmed-down CSV files.

    Args:
        processed_df (pd.DataFrame): Processed DataFrame.
    """
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    logger.info(f"Ensured that processed data directory exists: {PROCESSED_DATA_DIR}")

    # Save the full merged file
    processed_df.to_csv(FULL_MERGED_FILE, index=False)
    logger.info(f"Merged file saved to: {FULL_MERGED_FILE}")

    # Save the slimmed-down file
    slimmed_df = processed_df[['Id', 'Name_x', 'Role', 'Position', 'Team_x', 'Opp', 'base', 
                               'estimated_std_dev', 'team_share', 'Saber Team']].copy()
    slimmed_df.rename(columns={
        'Name_x': 'name',
        'Team_x': 'team',
        'Saber Team': 'implied_team_total'
    }, inplace=True)

    slimmed_output_file = SLIMMED_PROJECTIONS_FILE
    slimmed_df.to_csv(slimmed_output_file, index=False)
    logger.info(f"Slimmed file saved to: {slimmed_output_file}")
