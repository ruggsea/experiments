"""Random player implementation for baseline."""

import chess
import random
from .base import Player


class RandomPlayer(Player):
    """A player that makes random moves."""

    def __init__(self, elo: int = 500):
        """
        Initialize a random player.

        Args:
            elo: Nominal Elo (just for labeling, actual play is random)
        """
        super().__init__(elo)

    def select_piece_type(self, board: chess.Board) -> chess.PieceType:
        """
        Brain role: Pick a random piece type that has legal moves.

        Args:
            board: Current chess board state

        Returns:
            A random piece type that can move
        """
        # Get all piece types that have legal moves
        piece_types_with_moves = set()
        for move in board.legal_moves:
            piece_type = board.piece_type_at(move.from_square)
            if piece_type:
                piece_types_with_moves.add(piece_type)

        if piece_types_with_moves:
            return random.choice(list(piece_types_with_moves))

        # Fallback (should not happen)
        return chess.PAWN

    def select_move(self, board: chess.Board, piece_type: chess.PieceType) -> chess.Move:
        """
        Hand role: Pick a random legal move with the given piece type.

        Args:
            board: Current chess board state
            piece_type: The type of piece that must be moved

        Returns:
            A random legal move using the specified piece type
        """
        legal_moves_with_piece = [
            m for m in board.legal_moves
            if board.piece_type_at(m.from_square) == piece_type
        ]

        if legal_moves_with_piece:
            return random.choice(legal_moves_with_piece)

        # Fallback: any legal move
        legal_moves = list(board.legal_moves)
        if legal_moves:
            return random.choice(legal_moves)

        # Should never reach here if game is not over
        return list(board.legal_moves)[0]

    def __repr__(self):
        return f"RandomPlayer(elo={self.elo})"
