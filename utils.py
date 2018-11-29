#!/usr/bin/env python3
# utils.py
import numpy as np

SIZE = 19
EMPTY = 7
BLACK = 8
WHITE = 9
PASS = "pass"
OPPONENT = {BLACK:WHITE, WHITE:BLACK}
COL_NAMES = 'ABCDEFGHJKLMNOPQRST'


def coord_to_name(coord):
    return COL_NAMES[coord[1]] + str(SIZE - coord[0]).upper()


def name_to_coord(name):
    if name == 'resign' or name == PASS:
        return None
    return [SIZE - int(name[1:]), COL_NAMES.index(name[0])]


def color_name(color):
    return {BLACK:'b', WHITE:'w'}[color]


def sgf_move_to_coord(move):
    # ('b', (15, 16))
    # black four-three starting point
    row, col = move[1]
    return [SIZE - row - 1, col]


def clip(array):
    return np.clip(array, EMPTY, WHITE)


def fprint(x):
    print("rv => ", x)


def repr_recom(recoms):
    return ", ".join([m + "(" + str(r) + ")" for m, r in recoms]) if recoms is not None else str(None)
