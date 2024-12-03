# admin/tasks.py

import logging
from utils.file_handler import load_file_handlers
from sim.simulator import run_simulation_slate
from sim.utils.summarize_simulation_results import summarize_simulation_results
from sim.utils.save_simulation_results_to_csv import save_simulation_results_to_csv, sanitize_team_name
from sim.utils.move_old_simulation_files import move_old_simulation_files


logger = logging.getLogger(__name__)

def orchestrate_simulation_workflow(num_simulations: int = 100) -> dict:
    """
    Orchestrates the simulation workflow: loading data, running simulations, summarizing results, and saving to CSV.

    Args:
        num_simulations (int): The number of simulations to run.

    Returns:
        dict: Summary of simulation results.

    Raises:
        FileNotFoundError: If the processed data or game metadata is not loaded correctly.
    """
    logger.info("[Step 1] Loading and processing raw data...")
    file_handlers = load_file_handlers()

    # Assuming there's a file handler named 'read_and_process_raw_csvs'
    read_handler = file_handlers.get('read_and_process_raw_csvs')
    if not read_handler:
        logger.error("File handler 'read_and_process_raw_csvs' not found.")
        raise ImportError("File handler 'read_and_process_raw_csvs' not found.")

    processed_data, game_metadata = read_handler()

    if processed_data is None or game_metadata is None:
        logger.error("Processed data or game metadata is None. Ensure raw files are present and correctly formatted.")
        raise FileNotFoundError("Processed data or game metadata is None. Ensure raw files are present and correctly formatted.")

    # Optionally, add a 'game_id' to game_metadata if not present
    if 'game_id' not in game_metadata:
        game_metadata['game_id'] = 1  # Assign a default or derive from data

    # Ensure team names are present in game_metadata
    if 'team1_name' not in game_metadata or 'team2_name' not in game_metadata:
        logger.error("Game metadata must include 'team1_name' and 'team2_name'.")
        raise KeyError("Game metadata must include 'team1_name' and 'team2_name'.")

    logger.info("[Step 2] Running simulations...")
    try:
        slate = run_simulation_slate(processed_data, game_metadata, num_simulations)
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

