#!/usr/bin/env python3
# main.py
import npyscreen

from board import Board
from leelaz import leelaz
from utils import repr_recom
from game import game


class LeelayForm(npyscreen.FormBaseNew):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        y, x = self.useable_space()
        board = self.add(Board)

    def while_waiting(self):
        self.name = " | ".join([
                self.name.split(' | ')[0],
                str(leelaz.winrate()),
                str(leelaz.playout()),
                repr_recom(leelaz.recommendations())
            ])
        self.display()


def myFunction(*args):
    leelay = LeelayForm(name="black's turn")
    leelay.edit()


class Leelay(npyscreen.StandardApp):
    def onStart(self):
        self.addForm("MAIN", LeelayForm, name="black's turn")
        leelaz.start()

    def onCleanExit(self):
        leelaz.stop()


if __name__ == '__main__':
    # npyscreen.wrapper_basic(myFunction)
    leelay = Leelay()
    leelay.run()
