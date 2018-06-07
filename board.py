#!/usr/bin/env python3
import npyscreen
import random
import curses

class Board(npyscreen.SimpleGrid):
    def __init__(self, *args, **kwargs):
        super().__init__(column_width=3, col_margin=0, row_height=1, *args, **kwargs)
        self.edit_cell = [1, 1]

        self.values = []
        self.values.append(list(' abcdefghjklmnopqrst '))
        for x in range(19):
            row = []
            row.append(str(19-x))
            for y in range(19):
                if (x, y) in [(3,15),(9,15),(15,3),(9,3),(3,3),(15,15),(15,9),(9,9),(3,9)]:
                    row.append('+')
                else:
                    row.append('.')
            row.append(str(19-x))
            self.values.append(row)
        self.values.append(list(' abcdefghjklmnopqrst '))
        self.add_handlers({
            'u':                self.h_undo,
            'z':                self.h_play_move,
            'g':                self.h_gen_move,
            curses.KEY_UP:      self.h_cursor_up,
            curses.KEY_LEFT:    self.h_cursor_left,
            curses.KEY_DOWN:    self.h_cursor_down,
            curses.KEY_RIGHT:   self.h_cursor_right,
            'k':                self.h_cursor_up,
            'h':                self.h_cursor_left,
            'j':                self.h_cursor_down,
            'l':                self.h_cursor_right,
            '^K':               self.h_cursor_up_star,
            '^H':               self.h_cursor_left_star,
            '^J':               self.h_cursor_left_star,
            '^L':               self.h_cursor_right_star,
            curses.KEY_NPAGE:   self.h_cursor_top_left,
            curses.KEY_PPAGE:   self.h_cursor_bottom_right,
            curses.KEY_HOME:    self.h_cursor_top_left,
            curses.KEY_END:     self.h_cursor_bottom_right,
            ord('g'):           self.h_cursor_top_left,
            ord('G'):           self.h_cursor_bottom_right,
            'c':                self.h_cursor_tengen,
            curses.ascii.NL:    self.h_cursor_focus,
            curses.ascii.CR:    self.h_cursor_focus,
        })

    def h_undo(self, *args, **kwargs):
        pass

    def h_play_move(self, *args, **kwargs):
        # self.values[self.edit_cell[0]][self.edit_cell[1]] = 'O'
        pass

    def h_gen_move(self, *args, **kwargs):
        pass

    def h_cursor_up(self, *args, **kwargs):
        if self.edit_cell[0] > 1:
            self.edit_cell[0] -= 1

    def h_cursor_left(self, *args, **kwargs):
        if self.edit_cell[1] > 1:
            self.edit_cell[1] -= 1

    def h_cursor_down(self, *args, **kwargs):
        if self.edit_cell[0] <= 18:
            self.edit_cell[0] += 1

    def h_cursor_right(self, *args, **kwargs):
        if self.edit_cell[1] <= 18:
            self.edit_cell[1] += 1

    def h_cursor_up_star(self, *args, **kwargs):
        if self.edit_cell[0] > 16:
            self.edit_cell[0] = 16
        elif self.edit_cell[0] > 10:
            self.edit_cell[0] = 10
        elif self.edit_cell[0] > 4:
            self.edit_cell[0] = 4

    def h_cursor_left_star(self, *args, **kwargs):
        if self.edit_cell[1] > 16:
            self.edit_cell[1] = 16
        elif self.edit_cell[1] > 10:
            self.edit_cell[1] = 10
        elif self.edit_cell[1] > 4:
            self.edit_cell[1] = 4

    def h_cursor_down_star(self, *args, **kwargs):
        if self.edit_cell[0] < 4:
            self.edit_cell[0] = 4 
        elif self.edit_cell[0] < 10:
            self.edit_cell[0] = 10
        elif self.edit_cell[0] < 16:
            self.edit_cell[0] = 16

    def h_cursor_right_star(self, *args, **kwargs):
        if self.edit_cell[1] < 4:
            self.edit_cell[1] = 4 
        elif self.edit_cell[1] < 10:
            self.edit_cell[1] = 10
        elif self.edit_cell[1] < 16:
            self.edit_cell[1] = 16

    def h_cursor_top_left(self, *args, **kwargs):
        self.edit_cell = [1, 1]

    def h_cursor_bottom_right(self, *args, **kwargs):
        self.edit_cell = [19, 19]

    def h_cursor_tengen(self, *args, **kwargs):
        self.edit_cell = [10, 10]

    def h_cursor_focus(self, *args, **kwargs):
        pass
