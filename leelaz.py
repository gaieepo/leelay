#!/usr/bin/env python3
import os
import re
import time
import sys
import queue
from threading import Thread
from functools import reduce
from subprocess import Popen, PIPE, STDOUT

import yaml

from utils import fprint


class ReaderThread:
    def __init__(self, fd):
        self.queue = queue.Queue()
        self.fd = fd
        self.stopped = False
        self.winrate = None
        self.playouts = None

    def stop(self):
        self.stopped = True

    def loop(self, caller=None, debug=False):
        while not self.stopped and not self.fd.closed:
            line = None
            try:
                line = self.fd.readline().strip()
            except IOError:
                time.sleep(0.2)
                print("Readline error", file=sys.stderr)
                pass
            if line is not None and len(line) > 0:
                line = line.decode()
                if line.startswith("info"):
                    variations = line[5:].split(" info ")
                    total_playouts = sum(int(v.split()[3]) for v in variations)
                    self.playouts = total_playouts
                    self.winrate = reduce(
                            lambda rv, v: rv + (int(v[5]) / 100.0) * int(v[3]) / total_playouts,
                            [v.split() for v in variations],
                            0.0
                            )
                else:
                    self.queue.put(line)
                if debug:
                    print(caller + " => " + line)

    def readline(self):
        try:
            line = self.queue.get_nowait()
        except queue.Empty:
            return ""
        return line

    def read_all_lines(self):
        lines = []
        while True:
            try:
                line = self.queue.get_nowait()
            except queue.Empty:
                break
            lines.append(line)
        return lines


def start_reader_thread(fd, caller, debug=False):
    rt = ReaderThread(fd)
    def begin_loop():
        rt.loop(caller, debug)
    t = Thread(target=begin_loop)
    t.start()
    return rt


class Leelaz:
    def __init__(self, debug=None):
        self.p = None
        self.stdout_thread = None
        self.stderr_thread = None

        with open('config.yaml', 'r') as infile:
            self.conf = yaml.load(infile)

        self.debug = self.conf['debug']
        if debug is not None:
            self.debug = debug

    def __new__(cls, *args, **kwargs):
        singleton = cls.__dict__.get('__singleton__')
        if singleton is not None:
            return singleton
        cls.__singleton__ = singleton = object.__new__(cls)
        return singleton

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()

    def drain(self):
        so = self.stdout_thread.read_all_lines()
        se = self.stderr_thread.read_all_lines()
        return (so,se)

    def analyze(self):
        self.p.stdin.write(bytes('lz-analyze 10\n', 'utf-8'))
        self.p.stdin.flush()

    def send_command(self, cmd, expected_success_count=1, drain=True, timeout=20):
        self.p.stdin.write(bytes(cmd + '\n', 'utf-8'))
        self.p.stdin.flush()

        sleep_per_try = 0.1
        tries = 0
        success_count = 0

        while tries * sleep_per_try <= timeout and self.p is not None:
            time.sleep(sleep_per_try)
            tries += 1
            while True:
                s = self.stdout_thread.readline()
                if s.count('=') == 1:
                    success_count += 1
                    if success_count >= expected_success_count:
                        if drain:
                            self.drain()
                        return s
                if s == '':
                    break
        raise Exception("Failed to send command '%s' to LeelaZero" % (cmd))

    def start(self):
        gpus = []
        for _ in self.conf['gpu']:
            gpus += ['--gpu', str(_)]
        p = Popen(['./leelaz', '-g', '-w' + self.conf['weight-file'], '-t', str(self.conf['thread'])] + gpus, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        self.p = p
        self.stdout_thread = start_reader_thread(p.stdout, caller='stdout', debug=self.debug)
        self.stderr_thread = start_reader_thread(p.stderr, caller='stderr', debug=self.debug)

        self.send_command("time_settings 0 " + str(self.conf['gen-move-seconds']) + " 1")
        self.analyze()

    def play_move(self, color, move):
        self.send_command("play %s %s" % (color, move))
        self.analyze()

    def gen_move(self, color):
        time_limit = self.conf['gen-move-seconds']
        self.p.stdin.write(bytes('genmove %s\n' % color, 'utf-8'))
        self.p.stdin.flush()

        sleep_per_wait = 0.1
        waited = 0
        outs, errs = [], []
        while waited * sleep_per_wait < time_limit * 2  and self.p is not None:
            time.sleep(sleep_per_wait)
            so, se = self.drain()
            outs.extend(so)
            errs.extend(se)
            if len(so) == 1 and len(so[0]) > 1 and so[0].count('=') == 1:
                break
            waited += 1

        self.p.stdin.write(b'\n')
        self.p.stdin.flush()
        time.sleep(0.5)
        so, se = self.drain()

        self.analyze()

        return outs[-1].split()[1]

    def undo(self):
        self.send_command('undo')

    def winrate(self):
        rv = self.stdout_thread.winrate
        return "{0:.2f}".format(rv) if rv is not None else rv

    def playout(self):
        return self.stdout_thread.playouts

    def stop(self):
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
                print("Error when key in exit: ", str(e), file=sys.stderr)

            time.sleep(0.1)

            try:
                p.terminate()
            except OSError as e:
                print("Error when terminate process: ", str(e), file=sys.stderr)

# instantiate leelaz entity
leelaz = Leelaz()


if __name__ == '__main__':
    with Leelaz(debug=True) as leelaz:
        fprint(leelaz.gen_move('b'))
