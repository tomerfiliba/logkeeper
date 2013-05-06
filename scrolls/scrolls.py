import os
import thread
import sys
from contextlib import contextmanager
from datetime import datetime


class LogHandler(object):
    def process_record(self, record):
        raise NotImplementedError()

class RecordExtender(object):
    def extend_record(self, record):
        raise NotImplementedError()

class ProcInfoExtender(RecordExtender):
    def extend_record(self, record):
        record.update(pid = os.getpid(), tid = thread.get_ident())

_loggers_registry = {}

class AttrDict(dict):
    __slots__ = []
    __getattr__ = dict.__getitem__

class Logger(LogHandler, RecordExtender):
    class __metaclass__(type):
        def __call__(self, name):
            if name not in _loggers_registry:
                _loggers_registry[name] = type.__call__(self, name)
            return _loggers_registry[name] 
    
    INFO = "INFO"
    DEBUG = "DEBUG"
    WARNING = "WARNING"
    ERROR = "ERROR"
    LEVELS = (DEBUG, INFO, WARNING, ERROR)
    
    def __init__(self, name):
        self.name = name
        if "." in name:
            self._parent = Logger(name.rsplit(".", 1)[0])
        else:
            self._parent = RootLogger
        self._nesting = 0
        self._handlers = {}
        self._extenders = []
    
    def __repr__(self):
        return "Logger(%r)" % (self.name,)

    def add_handler(self, **handlers):
        for level, handler in handlers.items():
            level = level.upper()
            if level not in self.LEVELS:
                raise ValueError("Invalid level %r" % (level,))
            if level not in self._handlers:
                self._handlers[level] = []
            self._handlers[level].append(handler)
    def add_extender(self, extender):
        self._extenders.append(extender)
    def sublogger(self, name):
        return Logger("%s.%s" % (self.name, name))

    def unparent(self, parent):
        self._parent = parent
    def reparent(self, parent):
        self._parent = parent
    def extend_record(self, record):
        for ext in self._extenders:
            ext.extend_record(record)
        if self._parent:
            self._parent.extend_record(record)
    def process_record(self, record):
        for handler in self._handlers.get(record["level"], ()):
            handler.process_record(record)
        if self._parent:
            self._parent.process_record(record)

    def log(self, level, msg, args):
        record = AttrDict(level = level, name = self.name, msg = msg, args = args, 
            time = datetime.now(), nesting = self._nesting)
        self.extend_record(record)
        self.process_record(record)

    def debug(self, msg, *args):
        self.log(self.DEBUG, msg, args)
    def info(self, msg, *args):
        self.log(self.INFO, msg, args)
    def warning(self, msg, *args):
        self.log(self.WARNING, msg, args)
    def error(self, msg, *args):
        self.log(self.ERROR, msg, args)
    def exception(self, msg, *args):
        self.log(self.ERROR, msg, args)

    @contextmanager
    def section(self, title, *args):
        self.info(title, *args)
        self._nesting += 1
        try:
            yield
        finally:
            self._nesting -= 1

class StackedHandler(LogHandler):
    def __init__(self):
        pass

class LogFormatter(LogHandler):
    def process_record(self, record):
        pass

class TextFormatter(LogHandler):
    ANSI_COLORS = AttrDict(
        reset = b"\1b[0m",
        fg_black = b"\x1b[30m",
        fg_grey = b"\x1b[1;30m",
        fg_red = b"\x1b[31m",
        fg_bold_red = b"\x1b[1;31m",
        fg_green = b"\x1b[32m",
        fg_bold_green = b"\x1b[1;32m",
        fg_yellow = b"\x1b[33m",
        fg_bold_yellow = b"\x1b[1;33m",
        fg_blue = b"\x1b[34m",
        fg_bold_blue = b"\x1b[1;34m",
        fg_magenta = b"\x1b[35m",
        fg_bold_magenta = b"\x1b[1;35m",
        fg_cyan = b"\x1b[36m",
        fg_bold_cyan = b"\x1b[1;36m",
        fg_white = b"\x1b[37m",
        fg_bold_white = b"\x1b[1;37m",
        bg_black = b"\x1b[40m",
        bg_grey = b"\x1b[40m",
        bg_red = b"\x1b[41m",
        bg_green = b"\x1b[42m",
        bg_yellow = b"\x1b[43m",
        bg_blue = b"\x1b[44m",
        bg_magenta = b"\x1b[45m",
        bg_cyan = b"\x1b[46m",
        bg_white = b"\x1b[47m",
    )
    for k in ANSI_COLORS.keys():
        if k.startswith("fg_"):
            ANSI_COLORS[k[3:]] = ANSI_COLORS[k]
    
    LEVEL_COLORS = AttrDict({
        Logger.INFO : "white",
        Logger.WARNING : "yellow",
        Logger.ERROR : "red",
    })
    
    PREFIX_FORMAT = ("{colors.grey}[{record.time:%H:%M:%S} {colors.bold_white}{record.name} "
        "{colors[level_colors[record.level]]}{record.level}{colors.grey}] {colors.white}")
    
    def process_record(self, record):
        msg = record["msg"]
        if record["args"]:
            msg = msg.format(record["args"])
        print "%s%s" % (self.PREFIX_FORMAT.format(record = record, 
            colors = self.ANSI_COLORS, level_colors = self.LEVEL_COLORS), msg)

class FileHandler(LogHandler):
    def __init__(self, stream):
        self.stream = stream
    @classmethod
    def open(cls, filename, mode = "a"):
        return FileHandler(open(filename, mode))
    def process_record(self, record):
        self.stream.flush()

#class RotatingFileHandler(LogHandler):
#    def __init__(self, filename_pattern, num_of_files = 5, max_file_size = 1024 * 1024):
#        self.filename_pattern = filename_pattern
#        self.num_of_files = num_of_files
#        self.max_file_size = max_file_size
#        self.candidates = [filename_pattern % (i,) for i in range()]
#        
#        self._curr_file = None
#    def get_curr_file(self):
#        
#        
#        os.fstat(self._curr_file.fileno()).st_size
#        
#    def process_record(self, record):
#        pass



RootLogger = None
RootLogger = Logger("root")

console_handler = ConsoleHandler(sys.stderr, 
    colorize = sys.stderr.isatty() and sys.platform != "win32")

RootLogger.add_handler(info = console_handler, warning = console_handler, error = console_handler)
RootLogger.add_extender(ProcInfoExtender())



if __name__ == "__main__":
    foo = Logger("foo")
    foo.info("hello")
    








