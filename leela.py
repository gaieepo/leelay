#!/usr/bin/env python3
import os
import re
import time
import sys
from queue import Queue, Empty
from threading import Thread
from subprocess import Popen, PIPE, STDOUT

from util import *

# TODO:
# 1. Decorator for clear drain
# 3. Actual pondering is not happening
# 4. Komi, handicap, pass and resign

# Start a thread that perpetually reads from the given file descriptor
# and pushes the result on to a queue, to simulate non-blocking io. We
# could just use fcntl and make the file descriptor non-blocking, but
# fcntl isn't available on windows so we do this horrible hack.
DEBUG = False

class ReaderThread:
    def __init__(self, fd):
        self.queue = Queue()
        self.fd = fd
        self.stopped = False

    def stop(self):
        # No lock since this is just a simple bool that only ever changes one way
        self.stopped = True

    def loop(self):
        while not self.stopped and not self.fd.closed:
            line = None
            # fd.readline() should return due to eof once the process is closed
            # at which point
            try:
                line = self.fd.readline().strip()
            except IOError:
                time.sleep(0.2)
                print("Readline error", file=sys.stderr)
                pass
            if line is not None and len(line) > 0:
                line = line.decode()
                if DEBUG:
                    print('put: ', line)
                self.queue.put(line)

    def is_empty(self):
        return self.queue.empty()

    def readline(self):
        try:
            line = self.queue.get_nowait()
        except Empty:
            return ""
        return line

    def read_all_lines(self):
        lines = []
        while True:
            try:
                line = self.queue.get_nowait()
            except Empty:
                break
            lines.append(line)
        return lines

def start_reader_thread(fd):
    rt = ReaderThread(fd)
    def begin_loop():
        rt.loop()
    t = Thread(target=begin_loop)
    t.start()
    return rt

class CLI(object):
    def __init__(self, is_handicap_game=False, nobook=False, komi=6.5, time_limit=10, verbosity=2, gpu=0):
        self.p = None
        self.stdout_thread = None
        self.stderr_thread = None
        self.is_handicap_game = is_handicap_game
        self.nobook = nobook
        self.komi = komi
        self.time_limit = time_limit # seconds
        self.verbosity = verbosity
        self.gpu = gpu

    # Drain all remaining stdout and stderr current contents
    def drain(self):
        so = self.stdout_thread.read_all_lines()
        se = self.stderr_thread.read_all_lines()
        return (so,se)

    # Send command and wait for ack
    def send_command(self, cmd, expected_success_count=1, drain=True, timeout=20):
        self.p.stdin.write(bytes(cmd + '\n', 'utf-8'))
        self.p.stdin.flush()

        sleep_per_try = 0.1
        tries = 0
        success_count = 0

        while tries * sleep_per_try <= timeout and self.p is not None:
            time.sleep(sleep_per_try)
            tries += 1
            # Readline loop
            while True:
                s = self.stdout_thread.readline()
                # Leela follows GTP and prints a line starting with "=" upon success.
                if s.count('=') == 1:
                    success_count += 1
                    if success_count >= expected_success_count:
                        if drain:
                            self.drain()
                        return s
                # No output, so break readline loop and sleep and wait for more
                if s == '':
                    break
        raise Exception("Failed to send command '%s' to Leela" % (cmd))

    def start(self):
        if self.verbosity > 0:
            print("Starting leela...", file=sys.stderr)

        if self.nobook:
            p = Popen(['/usr/games/leela_gtp_opencl', '--gtp', '--gpu', str(self.gpu), '--nobook'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        else:
            p = Popen(['/usr/games/leela_gtp_opencl', '--gtp', '--gpu', str(self.gpu)], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        self.p = p
        self.stdout_thread = start_reader_thread(p.stdout)
        self.stderr_thread = start_reader_thread(p.stderr)

        # not safe to wait
        # might not enough memory
        # might lost
        time.sleep(3)

        if self.verbosity > 0:
            print("Setting komi %.1f to Leela" % (self.komi), file=sys.stderr)

        self.send_command('komi %.1f' % (self.komi))
        self.send_command('time_settings 0 %d 1' % (self.time_limit))

    def stop(self):
        if self.verbosity > 0:
            print("Stopping leela...", file=sys.stderr)

        if self.p is not None:
            p = self.p
            stdout_thread = self.stdout_thread
            stderr_thread = self.stderr_thread

            self.p = None
            self.stdout_thread = None
            self.stderr_thread = None

            stdout_thread.stop()
            stderr_thread.stop()

            try:
                p.stdin.write(b'exit\n')
            except IOError as e:
                print('Error when key in exit: ', str(e), file=sys.stderr)

            # not safe here as well
            # the termination logic is hardcoded
            time.sleep(0.1)

            try:
                p.terminate()
            except OSError as e:
                print('Error when terminate process: ', str(e), file=sys.stderr)

    def load_sgf(self, sgf):
        '''
        leela 0.11 can process exception so this method exception should be added
        '''
        sgf = os.path.expanduser(sgf)
        if self.verbosity > 0:
            print("Loaded %s" % sgf, file=sys.stderr)
        self.send_command('loadsgf %s' % (sgf))

    def clear_board(self):
        if self.verbosity > 0:
            print("Clear board", file=sys.stderr)
        self.send_command('clear_board')

    def show_board(self):
        self.send_command('showboard', drain=False)
        so, se = self.drain()
        return se

    def winrate(self):
        rate = self.send_command('winrate').split()[1]
        return rate

    def whoseturn(self):
        '''
        1. history pop
        2. showboard log
        '''
        board_info = self.show_board()
        turn = None # black or white
        for i in board_info:
            if i.count('to move') == 1:
                turn = i.split()[0].strip().lower()
        return turn 

    def add_move(self, color, pos):
        '''
        Handle pass
        '''
        color = get_color(color)
        pos = get_position(pos)
        if self.verbosity > 0:
            print("Play %s at %s" % (color, pos), file=sys.stderr)
        cmd = "play %s %s" % (color, pos)
        self.send_command(cmd)

    def play_move(self, pos):
        color = self.whoseturn()
        pos = get_position(pos)
        if self.verbosity > 0:
            print("Play %s at %s" % (color, pos), file=sys.stderr)
        self.send_command('play %s %s' % (color, pos))
    
    def undo(self):
        if self.verbosity > 0:
            print("Undo", file=sys.stderr)
        self.send_command('undo')

    def heatmap(self):
        self.send_command('heatmap', drain=False)
        so, se = self.drain()
        assert len(se) == 19 and len(se[0].split()) == 19
        return [list(map(int, s.split())) for s in se]

    def hotspots(self, number_of_candidates=3):
        heat_map = self.heatmap()
        candidates = []
        try:
            for i in range(19):
                for j in range(19):
                    candidates.append((heat_map[i][j], i, j))
        except IndexError:
            print("Something is wrong in processing heatmap")
            print(heat_map)
        candidates.sort(key=lambda candidate: candidate[0], reverse=True)
        return candidates[:number_of_candidates]

    def analyze(self, time_limit=None):
        '''
        since gen will change board state
        we can repick to choose secondary prefered move
        0. generate next move
        1. undo
        2. pick more prefered add_move
        '''
        actual, candidates = self.generate_move(time_limit=time_limit)
        self.undo()
        return (actual, candidates)

    def generate_move(self, time_limit=None):
        '''
        can apply decorator to each move and get feedback
        this one the entire flow is CUSTOMIZED
        '''
        time_limit = time_limit if time_limit else self.time_limit
        if self.verbosity > 1:
            print("Generating in %d seconds..." % time_limit, file=sys.stderr)
            print(self.whoseturn(), "to play", file=sys.stderr)

        # necessary for each move keep the time available, short and constant
        self.send_command('time_left black %d 1' % (time_limit))
        self.send_command('time_left white %d 1' % (time_limit))

        # this one does not start with '=' sign
        self.p.stdin.write(bytes('genmove %s\n' % (self.whoseturn()), 'utf-8'))
        self.p.stdin.flush()

        waited = 0
        outs, errs = [], []

        while waited < time_limit * 2 and self.p is not None:
            time.sleep(1)
            so, se = self.drain()
            outs.extend(so)
            errs.extend(se)
            if len(so) == 1 and so[0].count('=') == 1:
                break
            waited += 1

        self.p.stdin.write(b'\n')
        self.p.stdin.flush()
        time.sleep(1)
        so, se = self.drain()
        
        actual, candidates  = get_position(outs[0].split()[1]), self.extract_candidates(errs)

        if self.verbosity > 0:
            print('Chosen move: %s' % (actual), file=sys.stderr)

        return (actual, candidates)

    def extract_candidates(self, stderr):
        move_regex = r'^([A-Z][0-9]+) -> +([0-9]+) \(W: +(\-?[0-9]+\.[0-9]+)\%\).*$'
        bookmove_regex = r'([0-9]+) book moves'
        candidates = []
        for line in stderr:
            if self.verbosity > 1:
                print(line, file=sys.stderr)
            M = re.match(bookmove_regex, line)
            if M is not None:
                return []

            M = re.match(move_regex, line)
            if M is not None:
                pos = get_position(M.group(1))
                simulations = int(M.group(2))
                winrate = float(M.group(3))
                candidate = {
                    'pos': pos,
                    'simulations': simulations,
                    'winrate': winrate,
                }
                candidates.append(candidate)

        candidates = candidates[:3]
        return candidates

leela = CLI(nobook=False, gpu=1)
# leela = CLI(verbosity=0, gpu=1)
leela.start()
leela.load_sgf('sample.sgf')
print_board(leela.show_board())
leela.generate_move()
print_board(leela.show_board())
leela.stop()
