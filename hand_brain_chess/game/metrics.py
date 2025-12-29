"""Chess game metrics and analysis."""

import chess
import chess.engine
from typing import List, Tuple, Optional


def calculate_centipawn_loss(
    board_states: List[chess.Board],
    moves: List[chess.Move],
    engine: chess.engine.SimpleEngine,
    time_limit: float = 0.1
) -> Tuple[float, float]:
    """
    Calculate average centipawn loss for both sides.

    Args:
        board_states: List of board states (before each move)
        moves: List of moves made
        engine: Stockfish engine for analysis
        time_limit: Time limit per position analysis

    Returns:
        Tuple of (white_avg_cpl, black_avg_cpl)
    """
    white_losses = []
    black_losses = []

    for i, (board, move) in enumerate(zip(board_states, moves)):
        try:
            # Get best move evaluation
            result = engine.play(board, chess.engine.Limit(time=time_limit))
            best_move = result.move

            # Evaluate position after best move
            board_copy = board.copy()
            board_copy.push(best_move)
            info_best = engine.analyse(board_copy, chess.engine.Limit(time=time_limit))
            score_best = info_best.get("score")

            # Evaluate position after actual move
            board_copy = board.copy()
            board_copy.push(move)
            info_actual = engine.analyse(board_copy, chess.engine.Limit(time=time_limit))
            score_actual = info_actual.get("score")

            if score_best is not None and score_actual is not None:
                # Convert to centipawns from perspective of side to move
                cp_best = score_best.relative.score(mate_score=10000)
                cp_actual = score_actual.relative.score(mate_score=10000)

                if cp_best is not None and cp_actual is not None:
                    # Loss is difference (best - actual), negated because we evaluated after move
                    loss = -(cp_actual - cp_best)

                    if board.turn == chess.WHITE:
                        white_losses.append(max(0, loss))  # Only count losses, not gains
                    else:
                        black_losses.append(max(0, loss))

        except Exception:
            # Skip this position if analysis fails
            continue

    white_avg = sum(white_losses) / len(white_losses) if white_losses else 0
    black_avg = sum(black_losses) / len(black_losses) if black_losses else 0

    return white_avg, black_avg


def count_blunders(
    board_states: List[chess.Board],
    moves: List[chess.Move],
    engine: chess.engine.SimpleEngine,
    threshold: int = 100,
    time_limit: float = 0.1
) -> Tuple[int, int]:
    """
    Count number of blunders (moves losing > threshold centipawns).

    Args:
        board_states: List of board states (before each move)
        moves: List of moves made
        engine: Stockfish engine for analysis
        threshold: Centipawn threshold for blunder (default 100)
        time_limit: Time limit per position analysis

    Returns:
        Tuple of (white_blunders, black_blunders)
    """
    white_blunders = 0
    black_blunders = 0

    for i, (board, move) in enumerate(zip(board_states, moves)):
        try:
            # Get evaluation before move
            info_before = engine.analyse(board, chess.engine.Limit(time=time_limit))
            score_before = info_before.get("score")

            # Get evaluation after move
            board_copy = board.copy()
            board_copy.push(move)
            info_after = engine.analyse(board_copy, chess.engine.Limit(time=time_limit))
            score_after = info_after.get("score")

            if score_before is not None and score_after is not None:
                cp_before = score_before.relative.score(mate_score=10000)
                cp_after = score_after.relative.score(mate_score=10000)

                if cp_before is not None and cp_after is not None:
                    # Loss from perspective of player who moved
                    loss = -(cp_after - cp_before)

                    if loss > threshold:
                        if board.turn == chess.WHITE:
                            white_blunders += 1
                        else:
                            black_blunders += 1

        except Exception:
            continue

    return white_blunders, black_blunders


def calculate_position_complexity(board: chess.Board) -> float:
    """
    Calculate complexity of a position (number of legal moves).

    Args:
        board: Chess board state

    Returns:
        Number of legal moves
    """
    return float(board.legal_moves.count())
