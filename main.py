# main.py
import npyscreen
from board import Board

class LeelayForm(npyscreen.FormBaseNew):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        y, x = self.useable_space()
        # title = self.add(npyscreen.TitleText, name='Board Form Title')
        board = self.add(Board, max_height=2*(y//3))

def myFunction(*args):
    leelay = LeelayForm(name='Leelay Form')
    leelay.edit()

class Leelay(npyscreen.StandardApp):
    def onStart(self):
        self.addForm("MAIN", LeelayForm, name="Leelay Form")

if __name__ == '__main__':
    npyscreen.wrapper_basic(myFunction)
    # leelay = Leelay()
    # leelay.run()