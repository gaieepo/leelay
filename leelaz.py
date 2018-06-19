#!/usr/bin/env python3
import os
import re
import time
import sys
import queue
from threading import Thread
from subprocess import Popen, PIPE, STDOUT


class ReaderThread:
    def __init__(self, fd):
        self.queue = queue.Queue()
        self.fd = fd
        self.stopped = False

    def stop(self):
        self.stopped = True

    def loop(self, caller=None):
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
                self.queue.put(line)

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


def start_reader_thread(fd):
    rt = ReaderThread(fd)
    def begin_loop():
        rt.loop()
    t = Thread(target=begin_loop)
    t.start()
    return rt


class Leelaz:
    def __init__(self):
        self.p = None
        self.stdout_thread = None
        self.stderr_thread = None

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
        p = Popen(['./leelaz', '-g', '-wnetwork.gz', '-t', '8', '--gpu', '2', '--gpu', '3'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        self.p = p
        self.stdout_thread = start_reader_thread(p.stdout)
        self.stderr_thread = start_reader_thread(p.stderr)

        self.send_command("time_settings 0 5 1")

    def play_move(self, color, move):
        self.send_command("play %s %s" % (color, move))

    def gen_move(self, color):
        time_limit = 5
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
            if len(so) == 1 and so[0].count('=') == 1:
                break
            waited += 1

        self.p.stdin.write(b'\n')
        self.p.stdin.flush()
        time.sleep(0.5)
        so, se = self.drain()

        return outs[0].split()[1]

    def undo(self):
        self.send_command('undo')

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

leelaz = Leelaz()

if __name__ == '__main__':
    with Leelaz() as leelaz:
        print(leelaz.gen_move('b'))
