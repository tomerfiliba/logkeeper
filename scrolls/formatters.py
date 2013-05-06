from scrolls.base import LogHandler, AttrDict, Logger


class LogFormatter(LogHandler):
    __slots__ = ["sink"]
    def __init__(self, sink):
        self.sink = sink
    def process_record(self, record):
        self.sink.write(self.format_record(record))
    def format_record(self, record):
        raise NotImplementedError()

class TextFormatter(LogFormatter):
    ANSI_COLORS = AttrDict(
        reset = b"\x1b[0m",
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
        Logger.ERROR : "bold_red",
    })
    
    PREFIX_FORMAT = ("{colors.grey}[{record.time:%H:%M:%S}{colors.reset} "
        "{colors.bold_white}{record.name}{colors.reset}/"
        "{level_color}{record.level:7}{colors.grey}]{colors.reset} ")
    
    def format_record(self, record):
        msg = record["msg"]
        if record["args"]:
            msg = msg.format(record["args"])
        prefix = self.PREFIX_FORMAT.format(record = record, colors = self.ANSI_COLORS, 
            level_color = self.ANSI_COLORS[self.LEVEL_COLORS[record.level]]) 
        return "%s%s%s" % (prefix, "    " * record.nesting, msg)



