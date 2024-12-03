import os

# Configuration for data directories and file paths

RAW_DATA_DIR = os.getenv('RAW_DATA_DIR', 'data/raw/')
PROCESSED_DATA_DIR = os.getenv('PROCESSED_DATA_DIR', 'data/processed/')
FULL_MERGED_FILE = os.path.join(PROCESSED_DATA_DIR, 'merged_data.csv')
SLIMMED_PROJECTIONS_FILE = os.path.join(PROCESSED_DATA_DIR, 'slimmed_projections.csv')
