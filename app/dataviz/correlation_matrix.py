import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

def display(summary: dict) -> None:
    """
    Displays a correlation heatmap of players' simulated points.

    Args:
        summary (dict): Summary of simulation results containing player points.
    """
    st.header("Correlation Between Players' Simulated Points")

    player_points = summary.get('player_points', {})
    if not player_points:
        st.warning("No player points data available.")
        logger.warning("No player points data available.")
        return

    df = pd.DataFrame(player_points)
    df = df.dropna(axis=1, how='any')  # Ensure no missing data

    if df.empty:
        st.warning("Insufficient data to compute correlations.")
        logger.warning("Insufficient data to compute correlations.")
        return

    corr_matrix = df.corr()

    plt.figure(figsize=(12, 10))
    sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', linewidths=0.5)
    plt.title("Correlation Heatmap of Players' Simulated Points")
    st.pyplot(plt)
    logger.info("Correlation heatmap displayed successfully.")
