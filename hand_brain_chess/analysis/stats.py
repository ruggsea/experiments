"""Statistical analysis of experiment results."""

import pandas as pd
import scipy.stats as stats
from typing import Dict, List


def analyze_results(df: pd.DataFrame) -> Dict:
    """
    Perform statistical analysis on experiment results.

    Args:
        df: DataFrame with experiment results

    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'by_skill_gap': [],
        'by_elo_pair': [],
        'overall': {}
    }

    # Overall statistics
    strong_brain = df[df['strong_role'] == 'brain']['result'].mean()
    strong_hand = df[df['strong_role'] == 'hand']['result'].mean()

    overall_t, overall_p = stats.ttest_ind(
        df[df['strong_role'] == 'brain']['result'],
        df[df['strong_role'] == 'hand']['result']
    )

    analysis['overall'] = {
        'strong_brain_winrate': strong_brain,
        'strong_hand_winrate': strong_hand,
        'difference': strong_brain - strong_hand,
        't_statistic': overall_t,
        'p_value': overall_p,
        'significant': overall_p < 0.05
    }

    # Analysis by skill gap
    skill_gaps = sorted(df['skill_gap'].unique())

    for gap in skill_gaps:
        subset = df[df['skill_gap'] == gap]

        brain_results = subset[subset['strong_role'] == 'brain']['result']
        hand_results = subset[subset['strong_role'] == 'hand']['result']

        brain_mean = brain_results.mean()
        hand_mean = hand_results.mean()

        # Statistical test
        if len(brain_results) > 1 and len(hand_results) > 1:
            t_stat, p_val = stats.ttest_ind(brain_results, hand_results)
        else:
            t_stat, p_val = 0, 1.0

        # Effect size (Cohen's d)
        pooled_std = ((brain_results.std() ** 2 + hand_results.std() ** 2) / 2) ** 0.5
        cohens_d = (brain_mean - hand_mean) / pooled_std if pooled_std > 0 else 0

        analysis['by_skill_gap'].append({
            'skill_gap': gap,
            'brain_winrate': brain_mean,
            'hand_winrate': hand_mean,
            'difference': brain_mean - hand_mean,
            't_statistic': t_stat,
            'p_value': p_val,
            'cohens_d': cohens_d,
            'significant': p_val < 0.05,
            'n_games': len(subset)
        })

    # Analysis by specific Elo pairs
    for strong_elo in sorted(df['strong_elo'].unique()):
        for weak_elo in sorted(df['weak_elo'].unique()):
            if strong_elo > weak_elo:
                subset = df[(df['strong_elo'] == strong_elo) & (df['weak_elo'] == weak_elo)]

                if len(subset) > 0:
                    brain_results = subset[subset['strong_role'] == 'brain']['result']
                    hand_results = subset[subset['strong_role'] == 'hand']['result']

                    brain_mean = brain_results.mean()
                    hand_mean = hand_results.mean()

                    if len(brain_results) > 1 and len(hand_results) > 1:
                        t_stat, p_val = stats.ttest_ind(brain_results, hand_results)
                    else:
                        t_stat, p_val = 0, 1.0

                    analysis['by_elo_pair'].append({
                        'strong_elo': strong_elo,
                        'weak_elo': weak_elo,
                        'skill_gap': strong_elo - weak_elo,
                        'brain_winrate': brain_mean,
                        'hand_winrate': hand_mean,
                        'difference': brain_mean - hand_mean,
                        't_statistic': t_stat,
                        'p_value': p_val,
                        'significant': p_val < 0.05
                    })

    return analysis


def print_summary(analysis: Dict):
    """
    Print human-readable summary of analysis.

    Args:
        analysis: Analysis results from analyze_results()
    """
    print("\n" + "=" * 80)
    print("HAND AND BRAIN CHESS - EXPERIMENT RESULTS")
    print("=" * 80)

    # Overall results
    overall = analysis['overall']
    print("\nOVERALL RESULTS:")
    print(f"  Strong player as Brain: {overall['strong_brain_winrate']:.3f} win rate")
    print(f"  Strong player as Hand:  {overall['strong_hand_winrate']:.3f} win rate")
    print(f"  Difference:             {overall['difference']:+.3f}")
    print(f"  Statistical significance: p = {overall['p_value']:.4f} {'***' if overall['p_value'] < 0.001 else '**' if overall['p_value'] < 0.01 else '*' if overall['p_value'] < 0.05 else 'ns'}")

    if overall['difference'] > 0:
        print(f"\n  → Strong player performs BETTER as BRAIN (by {abs(overall['difference']):.1%})")
    elif overall['difference'] < 0:
        print(f"\n  → Strong player performs BETTER as HAND (by {abs(overall['difference']):.1%})")
    else:
        print(f"\n  → No significant difference between roles")

    # Results by skill gap
    print("\n" + "-" * 80)
    print("RESULTS BY SKILL GAP:")
    print("-" * 80)
    print(f"{'Gap':<8} {'Brain':<10} {'Hand':<10} {'Diff':<10} {'Effect':<10} {'p-value':<10} {'Sig':<5}")
    print("-" * 80)

    for result in analysis['by_skill_gap']:
        sig_marker = '***' if result['p_value'] < 0.001 else '**' if result['p_value'] < 0.01 else '*' if result['p_value'] < 0.05 else 'ns'
        print(f"{result['skill_gap']:<8} "
              f"{result['brain_winrate']:<10.3f} "
              f"{result['hand_winrate']:<10.3f} "
              f"{result['difference']:+<10.3f} "
              f"{result['cohens_d']:<10.2f} "
              f"{result['p_value']:<10.4f} "
              f"{sig_marker:<5}")

    print("-" * 80)

    # Interpretation
    print("\nINTERPRETATION:")
    positive_gaps = [r for r in analysis['by_skill_gap'] if r['difference'] > 0 and r['significant']]
    negative_gaps = [r for r in analysis['by_skill_gap'] if r['difference'] < 0 and r['significant']]

    if positive_gaps:
        gaps_str = ", ".join(str(r['skill_gap']) for r in positive_gaps)
        print(f"  • Strong-as-Brain significantly better for gaps: {gaps_str}")

    if negative_gaps:
        gaps_str = ", ".join(str(r['skill_gap']) for r in negative_gaps)
        print(f"  • Strong-as-Hand significantly better for gaps: {gaps_str}")

    if not positive_gaps and not negative_gaps:
        print(f"  • No significant differences found at any skill gap level")

    print("\n" + "=" * 80)
