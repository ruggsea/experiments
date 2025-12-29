"""Hand and Brain team implementation."""

import chess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..players.base import Player


class HandBrainTeam:
    """Represents a Hand and Brain team with two players."""

    def __init__(self, brain: 'Player', hand: 'Player'):
        """
        Initialize a Hand and Brain team.

        Args:
            brain: The player who selects piece types
            hand: The player who selects specific moves
        """
        self.brain = brain
        self.hand = hand

    def make_move(self, board: chess.Board) -> chess.Move:
        """
        Make a move using Hand and Brain protocol.

        Args:
            board: Current chess board state

        Returns:
            The move to make
        """
        # Brain picks the piece type
        piece_type = self.brain.select_piece_type(board)

        # Hand picks the specific move with that piece
        move = self.hand.select_move(board, piece_type)

        return move

    def __repr__(self):
        return f"HandBrainTeam(brain={self.brain}, hand={self.hand})"
