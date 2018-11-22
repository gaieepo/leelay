#!/usr/bin/env python3
# utils.py

SIZE = 19
EMPTY = 0
BLACK = 1
WHITE = 2
PASS = "pass"
OPPONENT = {BLACK:WHITE, WHITE:BLACK}
COL_NAMES = 'ABCDEFGHJKLMNOPQRST'


def fprint(x):
    print("rv => ", x)


def _coord_to_name(coord):
    return COL_NAMES[coord[1]] + str(SIZE - coord[0]).upper()


def _name_to_coord(name):
    if name == 'resign':
        return None
    return [SIZE - int(name[1:]), COL_NAMES.index(name[0])]


def _color_name(color):
    return {BLACK:'b', WHITE:'w'}[color]


def _sgf_move_to_coord(move):
    # ('b', (15, 16))
    # black four-three starting point
    row, col = move[1]
    return [SIZE - row - 1, col]
