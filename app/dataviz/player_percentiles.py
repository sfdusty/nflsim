import streamlit as st
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def display(summary: dict) -> None:
    """
    Displays percentile outcomes for all players.

    Args:
        summary (dict): Summary of simulation results containing player points.
    """
    st.header("Player Percentile Outcomes")

    player_points = summary.get('player_points', {})
    if not player_points:
        st.warning("No player points data available.")
        logger.warning("No player points data available.")
        return

    percentiles = [25, 50, 75, 85, 95, 99]
    data = []

    for player, points in player_points.items():
        points = [p for p in points if isinstance(p, (int, float, np.number))]
        if not points:
            continue
        percentile_values = np.percentile(points, percentiles)
        player_data = {'Player': player}
        for p, val in zip(percentiles, percentile_values):
            player_data[f"{p}th Percentile"] = val
        data.append(player_data)

    if not data:
        st.warning("No valid player data available to display percentiles.")
        logger.warning("No valid player data available to display percentiles.")
        return

    df_percentiles = pd.DataFrame(data)
    percentile_cols = [f"{p}th Percentile" for p in percentiles]

    # Ensure percentile columns are numeric
    for col in percentile_cols:
        df_percentiles[col] = pd.to_numeric(df_percentiles[col], errors='coerce')

    st.dataframe(df_percentiles.style.format("{:.2f}", subset=percentile_cols))
    logger.info("Player percentiles displayed successfully.")
