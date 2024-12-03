import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger(__name__)

def display(summary: dict) -> None:
    """
    Displays game scores statistics and distributions.

    Args:
        summary (dict): Summary of simulation results containing team scores.
    """
    st.header("Game Scores Analysis")

    team_scores = summary.get('team_scores', {})
    if not team_scores:
        st.warning("No team scores data available.")
        logger.warning("No team scores data available.")
        return

    for team, scores in team_scores.items():
        st.subheader(f"Team: {team}")
        df_scores = pd.DataFrame(scores, columns=['Score'])

        if df_scores.empty:
            st.warning(f"No score data available for {team}.")
            logger.warning(f"No score data available for {team}.")
            continue

        # Summary statistics
        st.write("### Summary Statistics")
        st.write(df_scores.describe())
        logger.info(f"Displayed summary statistics for {team}.")

        # Distribution plot
        st.write("### Score Distribution")
        fig, ax = plt.subplots()
        sns.histplot(df_scores['Score'], kde=True, bins=30, ax=ax, color='skyblue')
        ax.set_title(f"Distribution of Simulated Scores for {team}")
        ax.set_xlabel("Simulated Scores")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)
        logger.info(f"Displayed score distribution for {team}.")
