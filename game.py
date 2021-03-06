#!/usr/bin/env python3
import numpy as np
from sgfmill import sgf

from leelaz import leelaz

from utils import *


class _Group:
    """Represent a solidly-connected group.

    Public attributes:
        colour
        points
        is_surrounded

    Points are coordinate pairs (row, col).
    """
    pass


class Game:
    def __init__(self):
        # shared board object
        self.board = np.zeros((SIZE, SIZE), dtype=np.int)

        self.next_player = BLACK
        self._is_empty = False

        self._clear_board()
        self._init_history()

    def __new__(cls, *args, **kwargs):
        singleton = cls.__dict__.get('__singleton__')
        if singleton is not None:
            return singleton
        cls.__singleton__ = singleton = object.__new__(cls)
        return singleton

    def _clear_board(self):
        self.board.fill(EMPTY)

    def _init_history(self):
        self.history = []
        self.history.append((None, clip(self.board.copy())))

    def play_move(self, move, gen=False):
        if move is None:
            return False

        # no enforce ko rule
        opponent = OPPONENT[self.next_player]

        if move == PASS:
            self.history.append((PASS, clip(self.board.copy())))
            self.next_player = opponent
            return True
        if self.board[tuple(move)] in [BLACK, WHITE]:
            return False

        self.board[tuple(move)] = self.next_player
        self.history.append((list(move), clip(self.board.copy())))

        if not gen:
            leelaz.play_move(color_name(self.next_player), coord_to_name(move))
        self._is_empty = False
        surrounded = self._find_surrounded_groups(move)
        simple_ko_point = None
        if surrounded:
            if len(surrounded) == 1:
                to_capture = surrounded
                if len(to_capture[0].points) == SIZE * SIZE:
                    self._is_empty = True
            else:
                to_capture = [group for group in surrounded if group.color == opponent]
                if len(to_capture) == 1 and len(to_capture[0].points) == 1:
                    self_capture = [group for group in surrounded if group.color == self.next_player]
                    if len(self_capture[0].points) == 1:
                        (simple_ko_point,) = to_capture[0].points
            for group in to_capture:
                for r, c in group.points:
                    self.board[r, c] = EMPTY
        self.next_player = opponent
        return simple_ko_point

    def gen_move(self):
        move = name_to_coord(leelaz.gen_move(color_name(self.next_player)))
        self.play_move(move, gen=True)
        return move

    def undo(self):
        if len(self.history) > 1:
            leelaz.undo()
            self.history.pop()
            prev_move = list(self.history[-1][0]) if self.history[-1][0] else None
            self.board[:] = clip(self.history[-1][1].copy())
            self.next_player = OPPONENT[self.next_player]
            return prev_move
        return None

    def pass_move(self):
        leelaz.play_move(color_name(self.next_player), PASS)
        self.play_move(PASS)
        return list([0, 0])

    def open_sgf(self):
        self._init_history()

        with open(leelaz.conf['sgf-file'], 'rb') as f:
            game = sgf.Sgf_game.from_bytes(f.read())

        for node in game.get_main_sequence()[1:]:
            move = sgf_move_to_coord(node.get_move())
            self.play_move(move)
            yield move

    def _find_surrounded_groups(self, move):
        (r, c) = move
        surrounded = []
        handled = set()
        for (row, col) in [(r,c),(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
            if not ((0 <= row < SIZE) and (0 <= col < SIZE)):
                continue

            player = self.board[row, col]
            if player == EMPTY:
                continue

            stone = (row, col)
            if stone in handled:
                continue

            group = self._make_group(row, col, player)
            if group.is_surrounded:
                surrounded.append(group)
            handled.update(group.points)
        return surrounded

    def _make_group(self, row, col, color):
        points = set()
        is_surrounded = True
        to_handle = set()
        to_handle.add((row, col))
        while to_handle:
            point = to_handle.pop()
            points.add(point)
            r, c = point
            for neighbor in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                (r1, c1) = neighbor
                if not ((0 <= r1 < SIZE) and (0 <= c1 < SIZE)):
                    continue
                neigh_color = self.board[r1, c1]
                if neigh_color == EMPTY:
                    is_surrounded = False
                elif neigh_color == color:
                    if neighbor not in points:
                        to_handle.add(neighbor)
        group = _Group()
        group.color = color
        group.points = points
        group.is_surrounded = is_surrounded
        return group

# instantiate game entity
game = Game()
