#sim/models.py

import numpy as np
import logging

logger = logging.getLogger(__name__)

class Team:
    def __init__(self, name: str, implied_total: float):
        self.name = name
        self.implied_total = implied_total
        self.players = []
        self.simulated_scores = []
        logger.info(f"Initialized Team: {self.name} with implied total: {self.implied_total}")

    def simulate_scores(self, num_simulations: int, variability: float = 0.15) -> None:
        """
        Simulates team scores based on a lognormal distribution.

        Args:
            num_simulations (int): Number of simulations to run.
            variability (float): Variability parameter for the lognormal distribution.
        """
        logger.info(f"Simulating scores for {self.name} with variability {variability}")
        try:
            mu = np.log(self.implied_total) - 0.5 * np.log(1 + variability**2)
            sigma = np.sqrt(np.log(1 + variability**2))
            self.simulated_scores = np.random.lognormal(mean=mu, sigma=sigma, size=num_simulations)
            logger.info(f"Generated {num_simulations} simulated scores for {self.name}")
        except Exception as e:
            logger.error(f"Error simulating scores for {self.name}: {e}")
            raise
