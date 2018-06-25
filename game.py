#!/usr/bin/env python3
import numpy as np
from leelaz import leelaz

SIZE = 19
EMPTY = 0
BLACK = 1
WHITE = 2
PASS = "pass"
OPPONENT = {BLACK:WHITE, WHITE:BLACK}
COL_NAMES = 'ABCDEFGHJKLMNOPQRST'


class _Group:
    """Represent a solidly-connected group.

    Public attributes:
        colour
        points
        is_surrounded

    Points are coordinate pairs (row, col).
    """
    pass

def _coord_to_name(coord):
    return COL_NAMES[coord[1]] + str(SIZE - coord[0]).upper()

def _name_to_coord(name):
    if name == 'resign':
        return None
    return [SIZE - int(name[1:]), COL_NAMES.index(name[0])]

def _color_name(color):
    return {BLACK:'b', WHITE:'w'}[color]

class Game:
    def __init__(self):
        self.board = np.zeros((SIZE, SIZE), dtype=np.int)
        self.board.fill(EMPTY)
        self.next_player = BLACK
        self._is_empty = False
        self.history = []
        self.history.append((None, self.board.copy()))

    def play_move(self, move, gen=False):
        if move is None:
            return False

        # no enforce ko rule
        opponent = OPPONENT[self.next_player]

        if move == PASS:
            self.history.append((PASS, self.board.copy()))
            self.next_player = opponent
            return True
        if self.board[tuple(move)] != EMPTY:
            return False

        self.board[tuple(move)] = self.next_player
        self.history.append((list(move), self.board.copy()))

        if not gen:
            leelaz.play_move(_color_name(self.next_player), _coord_to_name(move))
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
        move = _name_to_coord(leelaz.gen_move(_color_name(self.next_player)))
        self.play_move(move, gen=True)
        return move

    def undo(self):
        if len(self.history) > 1:
            leelaz.undo()
            self.history.pop()
            prev_move = list(self.history[-1][0]) if self.history[-1][0] else None
            self.board[:] = self.history[-1][1].copy()
            self.next_player = OPPONENT[self.next_player]
            return prev_move
        return None

    def pass_move(self):
        leelaz.play_move(_color_name(self.next_player), "pass")
        self.play_move(PASS)
        return list([0, 0])

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

game = Game()
