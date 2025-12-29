"""Visualization of experiment results."""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from typing import Optional


def create_visualizations(df: pd.DataFrame, output_dir: str = "results"):
    """
    Create all visualizations for experiment results.

    Args:
        df: DataFrame with experiment results
        output_dir: Directory to save plots
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (12, 8)

    # 1. Heatmap of win rate difference
    create_heatmap(df, output_path)

    # 2. Line plot: Win rate vs skill gap
    create_line_plot(df, output_path)

    # 3. Bar chart: Optimal role by skill gap bucket
    create_bar_chart(df, output_path)

    # 4. Box plot: Distribution of results
    create_box_plot(df, output_path)

    print(f"\nVisualizations saved to {output_path}/")


def create_heatmap(df: pd.DataFrame, output_path: Path):
    """Create heatmap of win rate difference by Elo pairing."""
    # Pivot table: difference (brain - hand) for each Elo combination
    pivot_data = []

    for strong_elo in sorted(df['strong_elo'].unique()):
        for weak_elo in sorted(df['weak_elo'].unique()):
            if strong_elo > weak_elo:
                subset = df[(df['strong_elo'] == strong_elo) & (df['weak_elo'] == weak_elo)]
                if len(subset) > 0:
                    brain_wr = subset[subset['strong_role'] == 'brain']['result'].mean()
                    hand_wr = subset[subset['strong_role'] == 'hand']['result'].mean()
                    diff = brain_wr - hand_wr
                    pivot_data.append({
                        'strong_elo': strong_elo,
                        'weak_elo': weak_elo,
                        'difference': diff
                    })

    if not pivot_data:
        return

    pivot_df = pd.DataFrame(pivot_data)
    heatmap_data = pivot_df.pivot(index='weak_elo', columns='strong_elo', values='difference')

    plt.figure(figsize=(12, 10))
    sns.heatmap(heatmap_data, annot=True, fmt='.3f', cmap='RdBu_r', center=0,
                cbar_kws={'label': 'Win Rate Difference\n(Brain - Hand)'})
    plt.title('Strong Player Performance: Brain vs Hand\n(Positive = Brain Better, Negative = Hand Better)',
              fontsize=14, fontweight='bold')
    plt.xlabel('Strong Player Elo', fontsize=12)
    plt.ylabel('Weak Player Elo', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path / 'heatmap_winrate_difference.png', dpi=300, bbox_inches='tight')
    plt.close()


def create_line_plot(df: pd.DataFrame, output_path: Path):
    """Create line plot of win rate vs skill gap."""
    skill_gaps = sorted(df['skill_gap'].unique())
    brain_winrates = []
    hand_winrates = []
    brain_errors = []
    hand_errors = []

    for gap in skill_gaps:
        subset = df[df['skill_gap'] == gap]
        brain_results = subset[subset['strong_role'] == 'brain']['result']
        hand_results = subset[subset['strong_role'] == 'hand']['result']

        brain_winrates.append(brain_results.mean())
        hand_winrates.append(hand_results.mean())

        # Standard error
        brain_errors.append(brain_results.sem())
        hand_errors.append(hand_results.sem())

    plt.figure(figsize=(12, 8))
    plt.errorbar(skill_gaps, brain_winrates, yerr=brain_errors, marker='o', linewidth=2,
                 label='Strong as Brain', capsize=5, markersize=8)
    plt.errorbar(skill_gaps, hand_winrates, yerr=hand_errors, marker='s', linewidth=2,
                 label='Strong as Hand', capsize=5, markersize=8)

    plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='50% (Draw Rate)')
    plt.xlabel('Skill Gap (Elo)', fontsize=12, fontweight='bold')
    plt.ylabel('Win Rate (Strong Player Team)', fontsize=12, fontweight='bold')
    plt.title('Win Rate vs Skill Gap: Brain vs Hand Assignment', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11, loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path / 'lineplot_winrate_vs_gap.png', dpi=300, bbox_inches='tight')
    plt.close()


def create_bar_chart(df: pd.DataFrame, output_path: Path):
    """Create bar chart showing optimal role by skill gap bucket."""
    # Create skill gap buckets
    df_copy = df.copy()
    df_copy['gap_bucket'] = pd.cut(
        df_copy['skill_gap'],
        bins=[0, 200, 400, 600, 800, 1000, 1500, 3000],
        labels=['0-200', '200-400', '400-600', '600-800', '800-1000', '1000-1500', '1500+']
    )

    # Calculate win rates by bucket and role
    bucket_stats = []
    for bucket in df_copy['gap_bucket'].cat.categories:
        subset = df_copy[df_copy['gap_bucket'] == bucket]
        if len(subset) > 0:
            brain_wr = subset[subset['strong_role'] == 'brain']['result'].mean()
            hand_wr = subset[subset['strong_role'] == 'hand']['result'].mean()
            bucket_stats.append({
                'bucket': str(bucket),
                'brain': brain_wr,
                'hand': hand_wr,
                'difference': brain_wr - hand_wr
            })

    if not bucket_stats:
        return

    bucket_df = pd.DataFrame(bucket_stats)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Top: Win rates
    x = np.arange(len(bucket_df))
    width = 0.35

    ax1.bar(x - width/2, bucket_df['brain'], width, label='Strong as Brain', alpha=0.8)
    ax1.bar(x + width/2, bucket_df['hand'], width, label='Strong as Hand', alpha=0.8)
    ax1.set_ylabel('Win Rate', fontsize=12, fontweight='bold')
    ax1.set_title('Win Rate by Skill Gap Bucket', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(bucket_df['bucket'])
    ax1.legend(fontsize=11)
    ax1.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
    ax1.grid(True, alpha=0.3, axis='y')

    # Bottom: Difference
    colors = ['green' if d > 0 else 'red' if d < 0 else 'gray' for d in bucket_df['difference']]
    ax2.bar(x, bucket_df['difference'], color=colors, alpha=0.7)
    ax2.set_xlabel('Skill Gap (Elo)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Win Rate Difference\n(Brain - Hand)', fontsize=12, fontweight='bold')
    ax2.set_title('Optimal Role Assignment\n(Green = Brain Better, Red = Hand Better)',
                  fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(bucket_df['bucket'])
    ax2.axhline(y=0, color='black', linewidth=1)
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path / 'barchart_optimal_role.png', dpi=300, bbox_inches='tight')
    plt.close()


def create_box_plot(df: pd.DataFrame, output_path: Path):
    """Create box plot showing distribution of results."""
    plt.figure(figsize=(14, 8))

    # Prepare data
    plot_data = []
    for gap in sorted(df['skill_gap'].unique()):
        subset = df[df['skill_gap'] == gap]
        for role in ['brain', 'hand']:
            results = subset[subset['strong_role'] == role]['result']
            for result in results:
                plot_data.append({
                    'Skill Gap': gap,
                    'Role': f'Strong as {role.capitalize()}',
                    'Win Rate': result
                })

    plot_df = pd.DataFrame(plot_data)

    sns.boxplot(data=plot_df, x='Skill Gap', y='Win Rate', hue='Role', palette='Set2')
    plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='50% (Draw)')
    plt.title('Distribution of Win Rates by Skill Gap and Role Assignment',
              fontsize=14, fontweight='bold')
    plt.xlabel('Skill Gap (Elo)', fontsize=12, fontweight='bold')
    plt.ylabel('Win Rate (Strong Player Team)', fontsize=12, fontweight='bold')
    plt.legend(fontsize=11, loc='best')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_path / 'boxplot_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
