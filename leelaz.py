#!/usr/bin/env python3
class subprocess import Popen, PIPE, STDOUT

class ReaderThread:
    def __init__(self, fd):
        self.fd = fd
        self.queue = Queue()
        self.stopped = False

    def stop(self):
        self.stopped = True

    def loop(self):
        while not self.stopped and not self.fd.closed:
            line = None
            try:
                line = self.fd.readline().strip()
            except IOError:
                print("Readline error", file=sys.stderr)
            if line is not None and len(line) > 0:
                line = line.decode()
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

class Leelaz:
    def __init__(self):
        self.p = Popen(['./leelaz',
            '-g',
            '-wnetwork.gz'])
        self.stdout_thread = start_reader_thread(p.stdout)
        self.stderr_thread = start_reader_thread(p.stderr)
