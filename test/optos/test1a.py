import os
import pandas as pd
from opto_utils import (
    preprocess_player_pool,
    generate_projection_sets,
    display_player_exposures,ROSTER_REQUIREMENTS,
)
from builder import optimize_lineup


# Set up base directory dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MERGED_PROJECTIONS_FILE = os.path.join(DATA_DIR, "merged_projections.csv")

def main():
    # Load the merged projections
    print("Loading merged projections...")
    try:
        player_pool = pd.read_csv(MERGED_PROJECTIONS_FILE)
    except FileNotFoundError:
        print(f"Error: File not found at {MERGED_PROJECTIONS_FILE}")
        return

    # Preprocess player pool
    print("Preprocessing player pool...")
    player_pool = preprocess_player_pool(player_pool)

    # Set user parameters
    num_lineups = 10  # Number of lineups to generate
    num_projection_sets = 10  # Number of unique projection sets
    variance_range = 0.1  # Variance range for projections (e.g., ±10%)
    min_salary = 49500  # Minimum salary for a lineup
    max_salary = 50000  # Maximum salary for a lineup
    min_uniques = 2  # Minimum unique players between lineups

    # Generate projection sets with variance
    print(f"Generating {num_projection_sets} projection sets with ±{variance_range * 100}% variance...")
    projection_sets = generate_projection_sets(
        player_pool, num_sets=num_projection_sets, variance_range=variance_range
    )

    # Optimize lineups for each projection set
    all_lineups = []
    for i, projections in enumerate(projection_sets, start=1):
        print(f"Optimizing lineup set {i}/{num_projection_sets}...")
        lineups = optimize_lineup(
            projections,
            ROSTER_REQUIREMENTS,
            min_salary=min_salary,
            max_salary=max_salary,
            num_lineups=num_lineups,
            min_uniques=min_uniques,
        )
        all_lineups.extend(lineups)

    # Display player exposures across all lineups
    print("\nPlayer Exposures:")
    display_player_exposures(all_lineups)

if __name__ == "__main__":
    main()
