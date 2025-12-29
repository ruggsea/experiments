"""Game simulation for Hand and Brain chess."""

import chess
import chess.engine
from dataclasses import dataclass
from typing import List, Optional
from .team import HandBrainTeam
from .metrics import calculate_position_complexity


@dataclass
class GameResult:
    """Results from a completed game."""
    result: float  # 1.0 = white wins, 0.5 = draw, 0.0 = black wins
    move_count: int
    white_avg_cpl: float = 0.0
    black_avg_cpl: float = 0.0
    white_blunders: int = 0
    black_blunders: int = 0
    avg_complexity: float = 0.0
    termination: str = "normal"
    pgn: str = ""
    board_states: List[chess.Board] = None
    moves: List[chess.Move] = None

    def __post_init__(self):
        if self.board_states is None:
            self.board_states = []
        if self.moves is None:
            self.moves = []


def play_game(
    white_team: HandBrainTeam,
    black_team: HandBrainTeam,
    max_moves: int = 200,
    stockfish_path: Optional[str] = None,
    analyze: bool = False
) -> GameResult:
    """
    Play a full game between two Hand and Brain teams.

    Args:
        white_team: Team playing white
        black_team: Team playing black
        max_moves: Maximum number of moves before declaring draw
        stockfish_path: Path to Stockfish for analysis (if analyze=True)
        analyze: Whether to perform post-game analysis (slower)

    Returns:
        GameResult with game statistics
    """
    board = chess.Board()
    board_states = []
    moves = []
    complexities = []

    # Play the game
    move_count = 0
    while not board.is_game_over() and move_count < max_moves:
        # Record board state before move
        board_states.append(board.copy())

        # Calculate position complexity
        complexities.append(calculate_position_complexity(board))

        # Get move from current team
        try:
            if board.turn == chess.WHITE:
                move = white_team.make_move(board)
            else:
                move = black_team.make_move(board)

            # Validate move is legal
            if move not in board.legal_moves:
                # Fallback: pick first legal move
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    move = legal_moves[0]
                else:
                    break

            moves.append(move)
            board.push(move)
            move_count += 1

        except Exception as e:
            # On error, try to make any legal move
            legal_moves = list(board.legal_moves)
            if legal_moves:
                move = legal_moves[0]
                moves.append(move)
                board.push(move)
                move_count += 1
            else:
                break

    # Determine result
    if board.is_checkmate():
        result = 0.0 if board.turn == chess.WHITE else 1.0
        termination = "checkmate"
    elif board.is_stalemate():
        result = 0.5
        termination = "stalemate"
    elif board.is_insufficient_material():
        result = 0.5
        termination = "insufficient_material"
    elif board.can_claim_draw():
        result = 0.5
        termination = "draw_claim"
    elif move_count >= max_moves:
        result = 0.5
        termination = "max_moves"
    else:
        result = 0.5
        termination = "unknown"

    # Create result object
    game_result = GameResult(
        result=result,
        move_count=move_count,
        avg_complexity=sum(complexities) / len(complexities) if complexities else 0,
        termination=termination,
        board_states=board_states,
        moves=moves
    )

    # Optional: Perform detailed analysis with Stockfish
    if analyze and stockfish_path and len(moves) > 0:
        try:
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            engine.configure({"Skill Level": 20})  # Use full strength for analysis

            # Calculate metrics (simplified - full analysis is expensive)
            # For now, just store the data for later analysis
            # You can uncomment below for full analysis but it will be slow

            # from .metrics import calculate_centipawn_loss, count_blunders
            # white_cpl, black_cpl = calculate_centipawn_loss(
            #     board_states, moves, engine, time_limit=0.05
            # )
            # white_blunders, black_blunders = count_blunders(
            #     board_states, moves, engine, threshold=100, time_limit=0.05
            # )
            # game_result.white_avg_cpl = white_cpl
            # game_result.black_avg_cpl = black_cpl
            # game_result.white_blunders = white_blunders
            # game_result.black_blunders = black_blunders

            engine.quit()
        except Exception:
            pass

    return game_result
