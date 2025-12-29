"""Stockfish-based player implementation."""

import chess
import chess.engine
from typing import Optional
import random
from .base import Player


class StockfishPlayer(Player):
    """
    A player that uses Stockfish engine at a specific skill level.

    Skill level mapping (approximate):
    - Level 0: ~800 Elo
    - Level 5: ~1300 Elo
    - Level 10: ~1800 Elo
    - Level 15: ~2300 Elo
    - Level 20: ~3000+ Elo
    """

    # Mapping from Elo to Stockfish skill level (0-20)
    ELO_TO_SKILL = {
        800: 0,
        1000: 2,
        1200: 4,
        1400: 7,
        1600: 10,
        1800: 13,
        2000: 15,
        2200: 17,
        2400: 19,
        2600: 20,
        3000: 20,
    }

    def __init__(self, elo: int, stockfish_path: str, think_time: float = 0.1):
        """
        Initialize a Stockfish-based player.

        Args:
            elo: Target Elo rating
            stockfish_path: Path to Stockfish binary
            think_time: Time limit for engine analysis in seconds
        """
        super().__init__(elo)
        self.stockfish_path = stockfish_path
        self.think_time = think_time
        self.skill_level = self._elo_to_skill_level(elo)
        self._engine: Optional[chess.engine.SimpleEngine] = None

    def _elo_to_skill_level(self, elo: int) -> int:
        """Convert Elo rating to Stockfish skill level."""
        # Find closest Elo in mapping
        elos = sorted(self.ELO_TO_SKILL.keys())
        if elo <= elos[0]:
            return self.ELO_TO_SKILL[elos[0]]
        if elo >= elos[-1]:
            return self.ELO_TO_SKILL[elos[-1]]

        # Linear interpolation
        for i in range(len(elos) - 1):
            if elos[i] <= elo <= elos[i + 1]:
                ratio = (elo - elos[i]) / (elos[i + 1] - elos[i])
                skill = self.ELO_TO_SKILL[elos[i]] + ratio * (
                    self.ELO_TO_SKILL[elos[i + 1]] - self.ELO_TO_SKILL[elos[i]]
                )
                return int(round(skill))

        return 10  # Default to medium skill

    def _get_engine(self) -> chess.engine.SimpleEngine:
        """Get or create engine instance."""
        if self._engine is None:
            self._engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            self._engine.configure({"Skill Level": self.skill_level})
        return self._engine

    def select_piece_type(self, board: chess.Board) -> chess.PieceType:
        """
        Brain role: Get best move from engine and return its piece type.

        Args:
            board: Current chess board state

        Returns:
            The piece type of the engine's preferred move
        """
        engine = self._get_engine()

        try:
            result = engine.play(board, chess.engine.Limit(time=self.think_time))
            best_move = result.move

            if best_move is None:
                # Fallback: pick random legal move's piece type
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    move = random.choice(legal_moves)
                    return board.piece_type_at(move.from_square)
                return chess.PAWN

            piece_type = board.piece_type_at(best_move.from_square)
            return piece_type
        except Exception as e:
            # Fallback on error
            legal_moves = list(board.legal_moves)
            if legal_moves:
                move = random.choice(legal_moves)
                return board.piece_type_at(move.from_square)
            return chess.PAWN

    def select_move(self, board: chess.Board, piece_type: chess.PieceType) -> chess.Move:
        """
        Hand role: Given piece type, find best legal move with that piece.

        Args:
            board: Current chess board state
            piece_type: The type of piece that must be moved

        Returns:
            Best move using the specified piece type
        """
        # Get all legal moves with the specified piece type
        legal_moves_with_piece = [
            m for m in board.legal_moves
            if board.piece_type_at(m.from_square) == piece_type
        ]

        if not legal_moves_with_piece:
            # No legal moves with this piece type - should not happen in valid game
            # Return any legal move as fallback
            legal_moves = list(board.legal_moves)
            if legal_moves:
                return random.choice(legal_moves)
            # If no legal moves at all, the game is over
            return list(board.legal_moves)[0]  # Will raise if truly no moves

        if len(legal_moves_with_piece) == 1:
            return legal_moves_with_piece[0]

        # Use engine to evaluate each move and pick the best
        engine = self._get_engine()
        best_move = None
        best_score = None

        try:
            for move in legal_moves_with_piece:
                board.push(move)
                info = engine.analyse(board, chess.engine.Limit(time=self.think_time / len(legal_moves_with_piece)))
                score = info.get("score")
                board.pop()

                if score is not None:
                    # Convert score to centipawns from current player's perspective
                    cp_score = score.relative.score(mate_score=10000)
                    if cp_score is not None:
                        # Negate because we want score from the perspective of the player who just moved
                        cp_score = -cp_score
                        if best_score is None or cp_score > best_score:
                            best_score = cp_score
                            best_move = move

            if best_move is not None:
                return best_move
        except Exception:
            pass

        # Fallback: return random move from available piece type moves
        return random.choice(legal_moves_with_piece)

    def close(self):
        """Close the engine."""
        if self._engine is not None:
            self._engine.quit()
            self._engine = None

    def __del__(self):
        """Cleanup engine on deletion."""
        self.close()

    def __repr__(self):
        return f"StockfishPlayer(elo={self.elo}, skill={self.skill_level})"
