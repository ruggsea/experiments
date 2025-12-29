"""Base class for chess players in Hand and Brain experiments."""

from abc import ABC, abstractmethod
import chess


class Player(ABC):
    """Base class for a chess player at a given skill level."""

    def __init__(self, elo: int):
        """
        Initialize a player with a given Elo rating.

        Args:
            elo: The player's Elo rating
        """
        self.elo = elo

    @abstractmethod
    def select_piece_type(self, board: chess.Board) -> chess.PieceType:
        """
        Brain role: choose which piece type to move.

        Args:
            board: Current chess board state

        Returns:
            A piece type (PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING)
        """
        pass

    @abstractmethod
    def select_move(self, board: chess.Board, piece_type: chess.PieceType) -> chess.Move:
        """
        Hand role: given a piece type, choose the specific move.

        Args:
            board: Current chess board state
            piece_type: The type of piece that must be moved

        Returns:
            A legal move using the specified piece type
        """
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(elo={self.elo})"
