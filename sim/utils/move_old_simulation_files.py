# sim/utils/move_old_simulation_files.py

import logging
import os
import shutil

logger = logging.getLogger(__name__)

def move_old_simulation_files(simulation_dir: str = 'data/simulations/', backup_dir: str = 'data/simulations/backup/'):
    """
    Moves existing simulation CSV files to the backup directory.

    Args:
        simulation_dir (str): Directory containing current simulation CSV files.
        backup_dir (str): Directory where backup CSV files will be stored.
    """
    logger.info("Moving old simulation files to backup...")
    os.makedirs(backup_dir, exist_ok=True)

    for filename in os.listdir(simulation_dir):
        if filename.endswith('.csv'):
            source_path = os.path.join(simulation_dir, filename)
            destination_path = os.path.join(backup_dir, filename)
            try:
                shutil.move(source_path, destination_path)
                logger.info(f"Moved {filename} to backup.")
            except Exception as e:
                logger.error(f"Failed to move {filename} to backup: {e}")

