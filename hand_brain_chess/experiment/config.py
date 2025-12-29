"""Experiment configuration."""

from dataclasses import dataclass
from typing import List


@dataclass
class ExperimentConfig:
    """Configuration for Hand and Brain experiments."""

    # Stockfish settings
    stockfish_path: str = "/usr/games/stockfish"
    think_time: float = 0.1  # seconds per move

    # Elo levels to test
    elo_levels: List[int] = None

    # Games per configuration
    games_per_config: int = 100

    # Maximum moves per game
    max_moves: int = 200

    # Output directory
    output_dir: str = "results"

    # Whether to perform detailed analysis (slower)
    analyze: bool = False

    # Random seed for reproducibility
    random_seed: int = 42

    def __post_init__(self):
        """Set defaults after initialization."""
        if self.elo_levels is None:
            self.elo_levels = [1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400]

    def get_experiments(self):
        """
        Generate list of all experiment configurations.

        Returns:
            List of dicts with experiment parameters
        """
        experiments = []
        for strong_elo in self.elo_levels:
            for weak_elo in self.elo_levels:
                if strong_elo > weak_elo:
                    experiments.append({
                        'strong_elo': strong_elo,
                        'weak_elo': weak_elo,
                        'skill_gap': strong_elo - weak_elo
                    })
        return experiments
