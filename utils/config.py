# utils/config.py

import os

# Define directories
RAW_DATA_DIR = os.path.join('data', 'raw')
PROCESSED_DATA_DIR = os.path.join('data', 'processed')
SIMULATIONS_DIR = os.path.join('data', 'simulations')
USER_UPLOADS_DIR = os.path.join('data', 'projections', 'user_uploads')

# Define output file paths
FULL_MERGED_FILE = os.path.join(PROCESSED_DATA_DIR, 'merged_data.csv')
SLIMMED_PROJECTIONS_FILE = os.path.join(PROCESSED_DATA_DIR, 'slimmed_projections.csv')

