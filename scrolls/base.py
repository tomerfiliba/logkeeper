import os
import thread
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
    __delattr__ = dict.__delitem__
    __setattr__ = dict.__setitem__

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


RootLogger = None
RootLogger = Logger("root")

#console_handler = ConsoleHandler(sys.stderr, 
#    colorize = sys.stderr.isatty() and sys.platform != "win32")
#RootLogger.add_handler(info = console_handler, warning = console_handler, error = console_handler)
RootLogger.add_extender(ProcInfoExtender())



if __name__ == "__main__":
    foo = Logger("foo")
    foo.info("hello")
    








