import sys
import traceback
import os
import thread
import time
from contextlib import contextmanager
from datetime import datetime

_logger_registry = {}


class LogFormatter(object):
    pass

class LogHandler(object):
    def process_record(self, record):
        raise NotImplementedError()

#class TextualFormatter(LogHandler):
#    def __init__(self, prefix_fmt = "[%(time)s %(logger)s/%(level)s]", date_fmt = "%H:%M:%S"):
#        self.prefix_fmt = prefix_fmt
#        self.date_fmt = date_fmt

class FileHandler(LogHandler):
    def __init__(self):
        pass
    def process_record(self, record):
        pass

class ConsoleHandler(LogHandler):
    def __init__(self, stream = sys.stderr, prefix_fmt = "[%(time)s %(logger)s/%(level)s]", date_fmt = "%H:%M:%S"):
        self.stream = stream
        self.prefix_fmt = prefix_fmt
        self.date_fmt = date_fmt
    
    def process_record(self, record):
        if self.stream.isatty():
            pass
        record["time"] = datetime.fromtimestamp(record["ts"]).strftime(self.date_fmt)
        prefix = self.prefix_fmt % record
        self.stream.write("%s %s%s\n" % (prefix, "    " * record["nesting"], record["msg"]))
        self.stream.flush()

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
                parts = name.split(".")
                for i in range(1, len(parts)):
                    parts[:i]
            
        return _logger_registry[name]
    
    def add_handler(self, level, handler):
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
        if args:
            try:
                msg %= args
            except (TypeError, ValueError) as ex:
                msg = "%s\n%r - %s" % (msg, args, ex)
        record = {"level" : level, "logger" : self.name, "ts" : time.time(), "pid" : os.getpid(), 
            "tid" : thread.get_ident(), "msg" : msg, "frame" : None, "nesting" : self._nesting}
        
        if self._include_frame:
            f = sys._getframe()
            while f is not None and f.f_code.co_filename == __file__:
                f = f.f_back
            record["frame"] = f
        
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
        msg += "\n%s"
        args += (tbtext,)
        self.log("EXCEPTION", msg, *args)
    
    @contextmanager
    def step(self):
        self._nesting += 1
        try:
            yield
        finally:
            self._nesting -= 1

root = Logger("root")
console = ConsoleHandler()
root.add_handler("INFO", console)

if __name__ == "__main__":
    root.info("hello")
    with root.step():
        root.info("world")













