import sys
from scrolls.base import Logger, LogHandler, RecordExtender, RootLogger
from scrolls.formatters import LogFormatter, TextFormatter
from scrolls.sinks import LogSink, FileSink, RotatingFileSink


console = TextFormatter(FileSink(sys.stderr))
RootLogger.add_handlers(info = console, warning = console, error = console)


