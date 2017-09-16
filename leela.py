#!/usr/bin/env python3
# sgfanalyze.py my_game.sgf --leela /PATH/TO/LEELA.exe > my_game_analyzed.sgf
# leela = leela.CLI(board_size=board_size,
#                   executable=args.executable,
#                   is_handicap_game=is_handicap_game,
#                   komi=komi,
#                   seconds_per_search=args.seconds_per_search,
#                   verbosity=args.verbosity)

import os
import re
import time
# import hashlib
import sys
from queue import Queue, Empty
from threading import Thread
from subprocess import Popen, PIPE, STDOUT

# Start a thread that perpetually reads from the given file descriptor
# and pushes the result on to a queue, to simulate non-blocking io. We
# could just use fcntl and make the file descriptor non-blocking, but
# fcntl isn't available on windows so we do this horrible hack.
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
                line = self.fd.readline()
            except IOError:
                time.sleep(0.2)
                print("Readline error")
                pass
            if line is not None and len(line) > 0:
                self.queue.put(line)

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
    def __init__(self, is_handicap_game=False, komi=6.5, seconds_per_search=5, verbosity=2):
        self.p = None
        self.is_handicap_game = is_handicap_game
        self.komi = komi
        self.seconds_per_search = seconds_per_search + 1 # add one to account for lag time
        self.verbosity = verbosity

    # Send command and wait for ack
    def send_command(self, cmd, expected_success_count=1, drain=True, timeout=20):
        self.p.stdin.write(bytes(cmd + '\n', 'utf-8'))
        print("Command '"+cmd+"' is sent")
        self.p.stdin.flush()

        sleep_per_try = 1.0
        tries = 0
        success_count = 0

        while tries * sleep_per_try <= timeout and self.p is not None:
            time.sleep(sleep_per_try)
            tries += 1
            # Readline loop
            while True:
                s = self.stdout_thread.readline()
                # Leela follows GTP and prints a line starting with "=" upon success.
                if s.strip() == b'=':
                    success_count += 1
                    if success_count >= expected_success_count:
                        return
                # No output, so break readline loop and sleep and wait for more
                if s.strip() == b'\n':
                    break
        raise Exception("Failed to send command '%s' to Leela" % (cmd))

    def start(self):
        if self.verbosity > 0:
            print("Starting leela...", file=sys.stderr)

        p = Popen(['/usr/games/leela_gtp_opencl', '--gtp'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        self.p = p
        self.stdout_thread = start_reader_thread(p.stdout)
        self.stderr_thread = start_reader_thread(p.stderr)

        # not safe to wait
        # might not enough memory
        # might lost
        time.sleep(5)

        if self.verbosity > 0:
            print("Setting komi %.1f to Leela" % (self.komi), file=sys.stderr)

        self.send_command('heatmap')
        self.send_command('komi %.1f' % (self.komi))
        self.send_command('time_settings 0 %d 1' % (self.seconds_per_search))

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
                print('Error when key in exit: ', str(e))

            # not safe here as well
            # the termination logic is hardcoded
            time.sleep(0.1)

            try:
                p.terminate()
            except OSError as e:
                print('Error when terminate process: ', str(e))

# def __init__(self, is_handicap_game=False, komi=6.5, seconds_per_search=5, verbosity=2):
leela = CLI()
leela.start()
leela.stop()
