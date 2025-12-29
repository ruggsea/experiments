#!/usr/bin/env python3
"""
Hand and Brain Chess - Optimal Role Assignment Study

This script runs experiments to determine whether the stronger player
should be "Brain" (picks piece type) or "Hand" (picks move) in Hand and
Brain chess, and how this varies with skill gap.
"""

import argparse
import sys
from pathlib import Path

from .experiment import ExperimentConfig, run_experiment
from .analysis import analyze_results, print_summary, create_visualizations


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Hand and Brain Chess - Optimal Role Assignment Study',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick test with 10 games per config
  python main.py --games-per-config 10 --output results/test/

  # Full experiment with custom Stockfish path
  python main.py --stockfish-path /usr/local/bin/stockfish --games-per-config 100

  # Limited Elo range for faster execution
  python main.py --elo-levels 1200 1400 1600 1800 --games-per-config 50
        """
    )

    parser.add_argument(
        '--stockfish-path',
        type=str,
        default='/usr/games/stockfish',
        help='Path to Stockfish binary (default: /usr/games/stockfish)'
    )

    parser.add_argument(
        '--games-per-config',
        type=int,
        default=100,
        help='Number of games per configuration (default: 100)'
    )

    parser.add_argument(
        '--elo-levels',
        type=int,
        nargs='+',
        default=[1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400],
        help='Elo levels to test (default: 1000 1200 1400 1600 1800 2000 2200 2400)'
    )

    parser.add_argument(
        '--think-time',
        type=float,
        default=0.1,
        help='Think time per move in seconds (default: 0.1)'
    )

    parser.add_argument(
        '--max-moves',
        type=int,
        default=200,
        help='Maximum moves per game before draw (default: 200)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='results',
        help='Output directory for results (default: results/)'
    )

    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Perform detailed post-game analysis (slower)'
    )

    parser.add_argument(
        '--random-seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    parser.add_argument(
        '--skip-plots',
        action='store_true',
        help='Skip generating visualizations'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Validate Stockfish path
    stockfish_path = Path(args.stockfish_path)
    if not stockfish_path.exists():
        print(f"Error: Stockfish not found at {stockfish_path}", file=sys.stderr)
        print("Please install Stockfish or specify path with --stockfish-path", file=sys.stderr)
        print("\nOn Ubuntu/Debian: sudo apt-get install stockfish", file=sys.stderr)
        print("On macOS: brew install stockfish", file=sys.stderr)
        sys.exit(1)

    # Create configuration
    config = ExperimentConfig(
        stockfish_path=str(stockfish_path),
        think_time=args.think_time,
        elo_levels=args.elo_levels,
        games_per_config=args.games_per_config,
        max_moves=args.max_moves,
        output_dir=args.output,
        analyze=args.analyze,
        random_seed=args.random_seed
    )

    # Print configuration
    print("=" * 80)
    print("HAND AND BRAIN CHESS - EXPERIMENT CONFIGURATION")
    print("=" * 80)
    print(f"Stockfish path:     {config.stockfish_path}")
    print(f"Think time:         {config.think_time}s per move")
    print(f"Elo levels:         {config.elo_levels}")
    print(f"Games per config:   {config.games_per_config}")
    print(f"Max moves:          {config.max_moves}")
    print(f"Output directory:   {config.output_dir}")
    print(f"Detailed analysis:  {config.analyze}")
    print(f"Random seed:        {config.random_seed}")
    print("=" * 80)

    experiments = config.get_experiments()
    total_games = len(experiments) * config.games_per_config * 2
    print(f"\nThis will run {total_games} total games across {len(experiments)} configurations.")
    print(f"Estimated time: ~{total_games * config.think_time * 40 / 60:.1f} minutes")
    print("\nStarting experiment...\n")

    # Run experiment
    try:
        df = run_experiment(config)
    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError running experiment: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Analyze results
    print("\n" + "=" * 80)
    print("ANALYZING RESULTS")
    print("=" * 80)

    analysis = analyze_results(df)
    print_summary(analysis)

    # Save detailed analysis
    output_path = Path(config.output_dir)
    analysis_file = output_path / "analysis_summary.txt"

    with open(analysis_file, 'w') as f:
        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        print_summary(analysis)

        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        f.write(output)

    print(f"\nAnalysis summary saved to {analysis_file}")

    # Create visualizations
    if not args.skip_plots:
        print("\n" + "=" * 80)
        print("CREATING VISUALIZATIONS")
        print("=" * 80)
        try:
            create_visualizations(df, config.output_dir)
        except Exception as e:
            print(f"Warning: Could not create visualizations: {e}", file=sys.stderr)

    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE!")
    print("=" * 80)
    print(f"\nAll results saved to: {output_path.absolute()}")
    print(f"  - experiment_results.csv: Raw data")
    print(f"  - analysis_summary.txt: Statistical analysis")
    if not args.skip_plots:
        print(f"  - *.png: Visualizations")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
