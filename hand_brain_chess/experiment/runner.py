"""Experiment runner for Hand and Brain chess studies."""

import random
from dataclasses import dataclass
from typing import List, Dict
from tqdm import tqdm
import pandas as pd
from pathlib import Path

from ..players import StockfishPlayer
from ..game import HandBrainTeam, play_game, GameResult
from .config import ExperimentConfig


@dataclass
class ExperimentResult:
    """Results from a single game in the experiment."""
    game_id: int
    strong_elo: int
    weak_elo: int
    skill_gap: int
    strong_role: str  # "brain" or "hand"
    weak_role: str    # "brain" or "hand"
    white_team_config: str  # "strong_brain" or "strong_hand"
    color: str  # "white" or "black" (which color is the team with strong player)
    result: float  # From perspective of team with strong player
    move_count: int
    avg_complexity: float
    termination: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for DataFrame."""
        return {
            'game_id': self.game_id,
            'strong_elo': self.strong_elo,
            'weak_elo': self.weak_elo,
            'skill_gap': self.skill_gap,
            'strong_role': self.strong_role,
            'weak_role': self.weak_role,
            'white_team_config': self.white_team_config,
            'color': self.color,
            'result': self.result,
            'move_count': self.move_count,
            'avg_complexity': self.avg_complexity,
            'termination': self.termination,
        }


def run_experiment(config: ExperimentConfig) -> pd.DataFrame:
    """
    Run full Hand and Brain experiment.

    Args:
        config: Experiment configuration

    Returns:
        DataFrame with all game results
    """
    random.seed(config.random_seed)

    # Create output directory
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all experiment configurations
    experiments = config.get_experiments()

    all_results = []
    game_id = 0

    print(f"Running {len(experiments)} experiment configurations")
    print(f"Games per config: {config.games_per_config}")
    print(f"Total games: {len(experiments) * config.games_per_config * 2}")

    for exp in tqdm(experiments, desc="Experiments"):
        strong_elo = exp['strong_elo']
        weak_elo = exp['weak_elo']
        skill_gap = exp['skill_gap']

        # Create players (reuse engines for efficiency)
        strong_player = StockfishPlayer(strong_elo, config.stockfish_path, config.think_time)
        weak_player = StockfishPlayer(weak_elo, config.stockfish_path, config.think_time)

        # Test both configurations
        for config_name, strong_role, weak_role in [
            ("strong_brain", "brain", "hand"),
            ("strong_hand", "hand", "brain")
        ]:
            # Create teams based on configuration
            if strong_role == "brain":
                team_with_strong = HandBrainTeam(brain=strong_player, hand=weak_player)
            else:
                team_with_strong = HandBrainTeam(brain=weak_player, hand=strong_player)

            if weak_role == "brain":
                team_with_weak = HandBrainTeam(brain=weak_player, hand=strong_player)
            else:
                team_with_weak = HandBrainTeam(brain=strong_player, hand=weak_player)

            # Play games (alternate colors)
            for game_num in range(config.games_per_config):
                game_id += 1

                # Alternate which team plays white
                if game_num % 2 == 0:
                    white_team = team_with_strong
                    black_team = team_with_weak
                    color = "white"
                else:
                    white_team = team_with_weak
                    black_team = team_with_strong
                    color = "black"

                # Play game
                game_result = play_game(
                    white_team=white_team,
                    black_team=black_team,
                    max_moves=config.max_moves,
                    stockfish_path=config.stockfish_path,
                    analyze=config.analyze
                )

                # Convert result to perspective of strong player's team
                if color == "white":
                    result_from_strong_perspective = game_result.result
                else:
                    result_from_strong_perspective = 1.0 - game_result.result

                # Record result
                exp_result = ExperimentResult(
                    game_id=game_id,
                    strong_elo=strong_elo,
                    weak_elo=weak_elo,
                    skill_gap=skill_gap,
                    strong_role=strong_role,
                    weak_role=weak_role,
                    white_team_config=config_name if color == "white" else ("strong_hand" if config_name == "strong_brain" else "strong_brain"),
                    color=color,
                    result=result_from_strong_perspective,
                    move_count=game_result.move_count,
                    avg_complexity=game_result.avg_complexity,
                    termination=game_result.termination
                )

                all_results.append(exp_result.to_dict())

        # Clean up players
        strong_player.close()
        weak_player.close()

    # Convert to DataFrame
    df = pd.DataFrame(all_results)

    # Save results
    output_file = output_dir / "experiment_results.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to {output_file}")

    return df
