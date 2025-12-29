# Hand and Brain Chess - Optimal Role Assignment Study

An empirical study to determine whether the stronger player should be "Brain" (picks piece type) or "Hand" (picks specific move) in Hand and Brain chess, and how this varies with skill gap.

## Overview

Hand and Brain chess is a team chess variant where:
- **Brain**: Chooses which piece type to move (Pawn, Knight, Bishop, Rook, Queen, King)
- **Hand**: Chooses the specific move with that piece type

This project uses Stockfish at different skill levels to simulate players of varying strengths and systematically tests both role assignments across different skill gaps.

## Hypothesis

The hypothesis is that larger skill gaps favor strong=Brain (to constrain the weak player), but there may be a crossover point where strong=Hand becomes better.

## Installation

### Requirements

```bash
# Install Stockfish
# Ubuntu/Debian:
sudo apt-get install stockfish

# macOS:
brew install stockfish

# Install Python dependencies
pip install -r requirements.txt
```

### Quick Start

```bash
# Test run with 10 games per config
python main.py --games-per-config 10 --output results/test/

# Full experiment (100 games per config)
python main.py --games-per-config 100 --output results/full/

# Custom Stockfish path
python main.py --stockfish-path /usr/local/bin/stockfish
```

## Project Structure

```
hand_brain_chess/
├── players/
│   ├── base.py          # Player abstract base class
│   ├── stockfish.py     # Stockfish-based player
│   └── random.py        # Random player (baseline)
├── game/
│   ├── team.py          # HandBrainTeam implementation
│   ├── simulator.py     # Game simulation engine
│   └── metrics.py       # Performance metrics
├── experiment/
│   ├── config.py        # Experimental parameters
│   └── runner.py        # Experiment orchestration
├── analysis/
│   ├── stats.py         # Statistical analysis
│   └── plots.py         # Visualization generation
├── main.py              # Entry point
└── requirements.txt     # Dependencies
```

## Usage

### Command Line Options

```
--stockfish-path PATH    Path to Stockfish binary (default: /usr/games/stockfish)
--games-per-config N     Games per configuration (default: 100)
--elo-levels E1 E2 ...   Elo levels to test (default: 1000-2400)
--think-time SECONDS     Think time per move (default: 0.1)
--max-moves N            Max moves before draw (default: 200)
--output DIR             Output directory (default: results/)
--analyze                Perform detailed analysis (slower)
--random-seed N          Random seed (default: 42)
--skip-plots             Skip visualization generation
```

### Examples

```bash
# Quick test
python main.py --games-per-config 10 --elo-levels 1200 1400 1600

# Focused study on specific skill gaps
python main.py --elo-levels 1600 1800 2000 --games-per-config 200

# High quality analysis (slower)
python main.py --think-time 0.5 --analyze --games-per-config 100
```

## Output

The experiment produces:

1. **experiment_results.csv**: Raw data with columns:
   - game_id, strong_elo, weak_elo, skill_gap
   - strong_role (brain/hand), weak_role
   - result, move_count, avg_complexity, termination

2. **analysis_summary.txt**: Statistical analysis including:
   - Overall win rates by role assignment
   - Results by skill gap with p-values
   - Effect sizes (Cohen's d)
   - Interpretation and recommendations

3. **Visualizations** (PNG):
   - Heatmap of win rate difference by Elo pairing
   - Line plot of win rate vs skill gap
   - Bar chart of optimal role by skill gap bucket
   - Box plot of result distributions

## Research Questions

### Primary
Given skill gap X, should the stronger player be Brain or Hand?

### Secondary
- How does this interact with absolute skill level?
- Are there position types where the answer flips?
- Does the optimal assignment change during the game (opening/middlegame/endgame)?

## Implementation Details

### Stockfish Skill Levels

The mapping from Elo to Stockfish skill level (0-20):
- 1000 Elo ≈ Skill Level 2
- 1200 Elo ≈ Skill Level 4
- 1400 Elo ≈ Skill Level 7
- 1600 Elo ≈ Skill Level 10
- 1800 Elo ≈ Skill Level 13
- 2000 Elo ≈ Skill Level 15
- 2200 Elo ≈ Skill Level 17
- 2400 Elo ≈ Skill Level 19

### Hand Role Implementation

When the Hand role receives a piece type constraint, it:
1. Finds all legal moves with that piece type
2. Uses Stockfish to evaluate each move
3. Selects the best move from those options

### Brain Role Implementation

The Brain role:
1. Gets Stockfish's best move for the position
2. Returns the piece type of that move

This simulates a Brain player who "knows" the best piece to move but delegates the specific move choice to their partner.

## Performance

Approximate runtime (on modern CPU):
- 10 games/config, 8 Elo levels: ~5 minutes
- 100 games/config, 8 Elo levels: ~45 minutes
- 100 games/config, full range: ~2-3 hours

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Possible extensions:
- Maia chess engine integration for more human-like play
- Phase-dependent analysis (opening/middlegame/endgame)
- Position type classification (tactical vs positional)
- Mistake propagation analysis
- Alternative Brain strategies (e.g., random piece selection)

## Citation

If you use this code for research, please cite:

```
@software{hand_brain_chess_study,
  title = {Hand and Brain Chess: Optimal Role Assignment Study},
  author = {[Your Name]},
  year = {2025},
  url = {https://github.com/yourusername/hand-brain-chess}
}
```
