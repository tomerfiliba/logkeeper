class LogSink(object):
    def write(self, obj):
        raise NotImplementedError()

class FileSink(LogSink):
    def __init__(self, stream, flush = True):
        self.stream = stream
    def write(self, obj):
        # thread synchronization!
        line = str(obj).strip() + "\n"
        self.stream.write(line)
        self.stream.flush()

class RotatingFileSink(LogSink):
    def __init__(self, filename, num_of_files = 5, max_file_size = 1024 * 1024):
        self.filename = filename
        self.num_of_files = num_of_files
        self.max_file_size = max_file_size

class EmailSink(LogSink):
    def __init__(self, fromaddr, toaddr, server, subject = ""):
        pass

class SyslogSink(LogSink):
    def __init__(self, prefix):
        pass

class NTEventLogSink(LogSink):
    pass








