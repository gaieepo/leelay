#!/usr/bin/env python3
import npyscreen
import curses

from utils import *
from leelaz import leelaz
from game import game

STAR = '+'
STARS = ((3,15),(9,15),(15,3),(9,3),(3,3),(15,15),(15,9),(9,9),(3,9))
BOARD_UI = {BLACK:'O',WHITE:'O',EMPTY:'.'}
COLOR_NAMES = {BLACK:'black',WHITE:'white'}
RCM_TOP = '@'
RCM_TOP_COLOR = 'IMPORTANT'
RCM_OTHERS = '#'
RCM_OTHERS_COLOR = 'CONTROL'
COLORS = {BLACK:'DANGER',WHITE:'STANDOUT',EMPTY:'CURSOR'}


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

            ord('q'):           self.h_terminate_leelay,

            'o':                self.h_open_sgf
        })

    def custom_print_cell(self, actual_cell, cell_display_value):
        if cell_display_value:
            recoms = []
            if leelaz.recommendations() is not None:
                for r in leelaz.recommendations():
                    if name_to_coord(r[0]):
                        recoms.append(tuple(name_to_coord(r[0])))
            if actual_cell.grid_current_value_index in recoms:
                if actual_cell.grid_current_value_index == recoms[0]:
                    actual_cell.value, actual_cell.color = RCM_TOP, RCM_TOP_COLOR
                else:
                    actual_cell.value, actual_cell.color = RCM_OTHERS, RCM_OTHERS_COLOR
            elif actual_cell.grid_current_value_index in STARS \
                    and cell_display_value == str(EMPTY):
                actual_cell.value = STAR
                actual_cell.color = COLORS[EMPTY]
            else:
                actual_cell.value = BOARD_UI[int(cell_display_value)]
                actual_cell.color = COLORS[int(cell_display_value)]

    def h_undo(self, *args, **kwargs):
        move = self.game.undo()
        if move:
            self.edit_cell = move
            self._update_status("%s's turn" % COLOR_NAMES[self.game.next_player])

    def h_play_move(self, *args, **kwargs):
        self.game.play_move(self.edit_cell)
        self._update_status("%s's turn" % COLOR_NAMES[self.game.next_player])

    def h_gen_move(self, *args, **kwargs):
        move = self.game.gen_move()
        self.edit_cell = move
        self._update_status("%s's turn" % COLOR_NAMES[self.game.next_player])

    def h_pass(self, *args, **kwargs):
        move = self.game.pass_move()
        self.edit_cell = move
        self._update_status("%s's turn" % COLOR_NAMES[self.game.next_player])

    def _update_status(self, status):
        self.parent.name = status
        self.parent.display()

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

    def h_open_sgf(self, *args, **kwargs):
        for move in self.game.open_sgf():
            self.edit_cell = move
            self._update_status("%s's turn" % COLOR_NAMES[self.game.next_player])
