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

    def loop(self, flag=False, caller=None):
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
                if flag:
                    print(caller + "=>" + line)

    def readline(self):
        try:
            line = self.queue.get_nowait()
        except queue.Empty:
            print("Empty queue", file=sys.stdout)
            return ""
        return line

    def read_all_lines(self):
        lines = []
        while True:
            try:
                line = self.queue.get_nowait()
            except queue.Empty:
                print("Empty queue", file=sys.stdout)
                break
            lines.append(line)
        return lines


def start_reader_thread(fd, flag=False, caller=None):
    rt = ReaderThread(fd)
    def begin_loop():
        rt.loop(flag, caller)
    t = Thread(target=begin_loop)
    t.start()
    return rt


class Leelaz:
    def __init__(self):
        self.p = None
        self.stdout_thread = None
        self.stderr_thread = None

    def drain(self):
        so = self.stdout_thread.read_all_lines()
        se = self.stderr_thread.read_all_lines()
        return (so,se)

    def send_command(self, cmd):
        try:
            self.p.stdin.write(bytes(cmd + '\n', 'utf-8'))
            self.p.stdin.flush()
        except Exception as e:
            template = "Exception type: {0}"
            print(template.format(type(e).__name__))
            print("Failed to send command '%s' to Leela" % (cmd))

    def play_move(self, color, move):
        self.send_command("play " + color + " " + move)

    def gen_move(self, color):
        self.send_command("genmove " + color)

    def start(self):
        p = Popen(['./leelaz', '-g', '-wnetwork.gz'], stdout=PIPE, stdin=PIPE, stderr=PIPE)
        self.p = p
        self.stdout_thread = start_reader_thread(p.stdout, caller='stdout', flag=True)
        self.stderr_thread = start_reader_thread(p.stderr, caller='stderr', flag=True)

        self.send_command("time_settings 0 5 1")

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


if __name__ == '__main__':
    leelaz = Leelaz()
    leelaz.start()
