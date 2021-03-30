import sys

class IOProxy():
    '''
    Intercepts I/O operations and maintains a record with both.
    '''
    def __init__(self):
        '''
        Creates a record.
        '''
        self.record = ""
        return

    def start(self):
        '''
        Saves actual stdin/out, and replaces working stdin/out with proxy.
        '''
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        sys.stdin = self
        sys.stdout = self

    def __enter__(self):
        '''
        Saves actual stdin/out, and replaces working stdin/out with proxy.
        '''
        self.start()

    def stop(self):
        '''
        Switches back to actual stdin/out and trims hanging newline from record.
        '''
        sys.stdin = self.stdin
        sys.stdout = self.stdout
        self.record = self.record[:len(self.record) - 1]

    def __exit__(self, ex_type, ex_value, ex_traceback):
        '''
        Switches back to actual stdin/out and trims hanging newline from record.
        '''
        if ex_value:
            self.stdout.write(ex_traceback+"\n")
        self.stop()

    def write(self, content):
        '''
        Writes content to record and passes to actual stdout.
        '''
        self.record = self.record + content
        self.stdout.write(content)

    def writelines(self, lines):
        '''
        Writes lines to record and passes to actual stdout.
        '''        
        for line in lines:
            self.record = self.record + line
        self.stdout.writelines(lines)

    def read(self, size=-1):
        '''
        Reads content from actual stdin and writes to record.
        '''
        content = self.stdin.read(size)
        self.record = self.record + content
        return content

    def readline(self, size=-1):
        '''
        Reads line from actual stdin and writes to record.
        '''
        line = self.stdin.readline(size)
        self.record = self.record + line
        return line

    def flush(self):
        '''
        Flushes actual stdout buffer.
        '''
        self.stdout.flush()
