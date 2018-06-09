#!/usr/bin/env python3
import npyscreen
import curses
import numbers
import numpy as np
from leelaz import leelaz

SIZE = 19
EMPTY = 0
BLACK = 1
WHITE = 2
PASS_MOVE = None
OPPONENT = {BLACK:WHITE, WHITE:BLACK}
STAR = '+'
STARS = ((3,15),(9,15),(15,3),(9,3),(3,3),(15,15),(15,9),(9,9),(3,9))
COL_NAMES = 'ABCDEFGHJKLMNOPQRST'
BOARD_UI = {BLACK:'X',WHITE:'O',EMPTY:'.'}


class State:
    def __init__(self, stones, last_move_position, last_move_color, black_to_play, zobrist):
        self.stones = stones
        self.last_move_position = last_move_position
        self.last_move_color = last_move_color
        self.black_to_play = black_to_play
        self.zobrist = zobrist

class _Group:
    pass

def _coord_to_name(coord):
    return COL_NAMES[coord[1]] + str(SIZE - coord[0]).upper()

def _name_to_coord(name):
    return [SIZE - int(name[1:]), COL_NAMES.index(name[0])]

def _color_name(color):
    return {BLACK:'b', WHITE:'w'}[color]

class Game:
    def __init__(self):
        self.board = np.zeros((SIZE, SIZE), dtype=np.int)
        self.board.fill(EMPTY)
        self.next_player = BLACK
        self._is_empty = False

    def play_move(self, move):
        # no enforce ko rule
        opponent = OPPONENT[self.next_player]
        if self.board[tuple(move)] != EMPTY:
            return False
        self.board[tuple(move)] = self.next_player
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
        move = leelaz.gen_move(_color_name(self.next_player))
        self.board[tuple(_name_to_coord(move))] = self.next_player
        self.next_player = OPPONENT[self.next_player]


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

class Board(npyscreen.SimpleGrid):
    def __init__(self, *args, **kwargs):
        super().__init__(column_width=2, col_margin=0, row_height=1, *args, **kwargs)

        self.game = game
        self.values = self.game.board

        self.add_handlers({
            'u':                self.h_undo,
            ord(' '):           self.h_play_move,
            'z':                self.h_gen_move,
            'p':                self.h_pass,

            curses.KEY_UP:      self.h_move_line_up,
            curses.KEY_LEFT:    self.h_move_cell_left,
            curses.KEY_DOWN:    self.h_move_line_down,
            curses.KEY_RIGHT:   self.h_move_cell_right,
            'k':                self.h_move_line_up,
            'h':                self.h_move_cell_left,
            'j':                self.h_move_line_down,
            'l':                self.h_move_cell_right,
            'c':                self.h_move_tengen,

            '^K':               self.h_cursor_up_star,
            '^H':               self.h_cursor_left_star,
            '^J':               self.h_cursor_down_star,
            '^L':               self.h_cursor_right_star,

            curses.KEY_NPAGE:   self.h_move_page_down,
            curses.KEY_PPAGE:   self.h_move_page_up,
            curses.KEY_HOME:    self.h_show_beginning,
            curses.KEY_END:     self.h_show_end,
            ord('g'):           self.h_show_beginning,
            ord('G'):           self.h_show_end,

            curses.ascii.ESC:   self.h_terminate_leelay
        })

    def custom_print_cell(self, actual_cell, cell_display_value):
        if cell_display_value:
            actual_cell.value = '+' \
                    if actual_cell.grid_current_value_index in STARS \
                        and cell_display_value == str(EMPTY) \
                    else BOARD_UI[int(cell_display_value)]

    def h_undo(self, *args, **kwargs):
        # unable until history implemented as currently stateless
        pass

    def h_play_move(self, *args, **kwargs):
        self.game.play_move(self.edit_cell)

    def h_gen_move(self, *args, **kwargs):
        self.game.gen_move()

    def h_pass(self, *args, **kwargs):
        pass

    def h_cursor_up_star(self, *args, **kwargs):
        if self.edit_cell[0] > SIZE-4:
            self.edit_cell[0] = SIZE-4
        elif self.edit_cell[0] > 9:
            self.edit_cell[0] = 9
        elif self.edit_cell[0] > 3:
            self.edit_cell[0] = 3

    def h_cursor_left_star(self, *args, **kwargs):
        if self.edit_cell[1] > SIZE-4:
            self.edit_cell[1] = SIZE-4
        elif self.edit_cell[1] > 9:
            self.edit_cell[1] = 9
        elif self.edit_cell[1] > 3:
            self.edit_cell[1] = 3

    def h_cursor_down_star(self, *args, **kwargs):
        if self.edit_cell[0] < 3:
            self.edit_cell[0] = 3 
        elif self.edit_cell[0] < 9:
            self.edit_cell[0] = 9
        elif self.edit_cell[0] < SIZE-4:
            self.edit_cell[0] = SIZE-4

    def h_cursor_right_star(self, *args, **kwargs):
        if self.edit_cell[1] < 3:
            self.edit_cell[1] = 3 
        elif self.edit_cell[1] < 9:
            self.edit_cell[1] = 9
        elif self.edit_cell[1] < SIZE-4:
            self.edit_cell[1] = SIZE-4

    def h_move_tengen(self, *args, **kwargs):
        self.edit_cell = [9, 9]

    def h_terminate_leelay(self, *args, **kwargs):
        self.parent.parentApp.switchForm(None)

if __name__ == '__main__':
    pass
