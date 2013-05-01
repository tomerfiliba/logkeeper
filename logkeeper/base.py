import sys
import traceback
import os
import thread
from contextlib import contextmanager
from datetime import datetime
from logkeeper.console import console_formatter

_logger_registry = {}


class LogFormatter(object):
    pass

class LogHandler(object):
    def process_record(self, record):
        raise NotImplementedError()

class FileHandler(LogHandler):
    def __init__(self):
        pass
    def process_record(self, record):
        pass

class RotatingFileHandler(LogHandler):
    def __init__(self, prefix, num_of_files, max_file_size):
        pass

class ConsoleHandler(LogHandler):
    def __init__(self, stream = sys.stderr, prefix = "{time#dark_grey:%H:%M:%S} {logger} {level#gold:5}{']'#dark_grey} "):
        self.stream = stream
        self.prefix = prefix
    
    def process_record(self, record):
        console_formatter.format(self.prefix, **record)
        if record["nesting"]:
            console_formatter.format("    " * record["nesting"])
        lines = "\n        | ".join(record["msg"].strip().splitlines())
        console_formatter.format(lines + "\n", *record["args"])

class Logger(LogHandler):
    def __init__(self, name, parent = None):
        self.name = name
        self._nesting = 0
        self._parent = parent
        self._handlers = {}
        self._include_frame = False

    def __new__(cls, name, parent = None):
        if name not in _logger_registry:
            if parent is not None or "." not in name:
                _logger_registry[name] = object.__new__(cls, name, parent)
            else:
                parent, this = name.rsplit(".", 1)
                return cls(parent).sublogger(this)
        return _logger_registry[name]
    
    def add_handlers(self, **kwargs):
        for level, handler in kwargs.items():
            if level not in self._handlers:
                self._handlers[level] = []
            if handler not in self._handlers[level]:
                self._handlers[level].append(handler)
    
    def remove_handler(self, level, handler):
        if level in self._handlers and handler in self._handlers[level]:
            self._handlers[level].remove(handler)

    def process_record(self, record):
        for handler in self._handlers.get(record["level"], ()):
            handler.process_record(record)
    
    def sublogger(self, name):
        return Logger(("%s.%s" % (self.name, name)) if self.name else name, self)
    
    def log(self, level, msg, *args):
        record = {"logger" : self.name, "level" : level, "time" : datetime.now(), "pid" : os.getpid(), 
            "tid" : thread.get_ident(), "msg" : msg, "args" : args, "nesting" : self._nesting}

        self.process_record(record)
        if self._parent:
            self._parent.process_record(record)
    
    def debug(self, msg, *args):
        self.log("DEBUG", msg, *args)
    def info(self, msg, *args):
        self.log("INFO", msg, *args)
    def warn(self, msg, *args):
        self.log("WARN", msg, *args)
    warning = warn
    def error(self, msg, *args):
        self.log("ERROR", msg, *args)
    def exception(self, msg, *args, **kwargs):
        exc_info = kwargs.pop("exc_info", sys.exc_info())
        tbtext = "".join(traceback.format_exception(*exc_info))
        self.log("EXC", msg + "\n" + tbtext, *args)
    
    @contextmanager
    def step(self):
        self._nesting += 1
        try:
            yield
        finally:
            self._nesting -= 1

root = Logger("root")
info_console_hdlr = ConsoleHandler()
warn_console_hdlr = ConsoleHandler(prefix = "{time#dark_grey:%H:%M:%S} {logger} {level#yellow:5}{']'#dark_grey} ")
err_console_hdlr = ConsoleHandler(prefix = "{time#dark_grey:%H:%M:%S} {logger} {level#white,red:5}{']'#dark_grey} ")
root.add_handlers(INFO = info_console_hdlr, WARN = warn_console_hdlr, 
    ERROR = err_console_hdlr, EXC = err_console_hdlr)

if __name__ == "__main__":
    root.info("hello")
    root.debug("invisible")
    with root.step():
        root.info("world")
        with root.step():
            root.info("zolrd")
        root.error("oh no!")
        root.info("oops")
        try:
            1/0
        except Exception:
            root.exception("oh my god")
    root.warn("loops")






