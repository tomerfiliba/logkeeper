import sys
from contextlib import contextmanager
from string import Formatter


class BaseStyler(object):
    def __init__(self, fileobj = sys.stdout, encoding = "utf8"):
        self.fileobj = fileobj
        self.encoding = encoding
    @contextmanager
    def colored(self, fg = None, bg = None):
        try:
            yield
        finally:
            pass
    def write(self, text):
        self.fileobj.write(text.encode(self.encoding))
    def writeln(self, text):
        self.write(text + "\n")


class ANSIStyler(BaseStyler):
    FG_COLOR_MAP = dict(
        black = b"30",
        grey = b"1;30",
        red = b"31",
        bold_red = b"1;31",
        green = b"32",
        bold_green = b"1;32",
        yellow = b"33",
        bold_yellow = b"1;33",
        blue = b"34",
        bold_blue = b"1;34",
        magenta = b"35",
        bold_magenta = b"1;35",
        cyan = b"36",
        bold_cyan = b"1;36",
        white = b"37",
        bold_white = b"1;37",
    )
    BG_COLOR_MAP = dict(
        black = b"40",
        grey = b"40",
        red = b"41",
        bold_red = b"41",
        green = b"42",
        bold_green = b"42",
        yellow = b"43",
        bold_yellow = b"43",
        blue = b"44",
        bold_blue = b"44",
        magenta = b"45",
        bold_magenta = b"45",
        cyan = b"46",
        bold_cyan = b"46",
        white = b"47",
        bold_white = b"47",
    )

    @contextmanager
    def colored(self, fg = None, bg = None):
        codes = []
        if fg:
            fg = self.FG_COLOR_MAP.get(fg.strip().lower().replace(" ", "_").replace("-", "_"), b"")
        if bg:
            bg = self.BG_COLOR_MAP.get(bg.strip().lower().replace(" ", "_").replace("-", "_"), b"")
        if fg:
            codes.append(fg)
        if bg:
            codes.append(bg)
        self.fileobj.write(b"\x1b[%sm" % (b";".join(codes),))

        try:
            yield
        finally:
            self.fileobj.write(b"\x1b[0m")


if sys.platform == "win32":
    from ctypes import windll, Structure, POINTER, byref
    from ctypes.wintypes import BOOL, HANDLE, SHORT, WORD, DWORD
    
    class COORD(Structure):
        _fields_ = [
            ("X", SHORT),
            ("Y", SHORT),
        ]
    
    class SMALL_RECT(Structure):
        _fields_ = [
            ("left", SHORT),
            ("top", SHORT),
            ("right", SHORT),
            ("bottom", SHORT),
        ]
    
    class CONSOLE_SCREEN_BUFFER_INFO(Structure):
        _fields_ = [
            ("size", COORD),
            ("cursorPosition", COORD),
            ("attributes", WORD),
            ("window", SMALL_RECT),
            ("maximumWindowSize", COORD),
        ]
    
    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE = -12
    
    GetStdHandle = windll.kernel32["GetStdHandle"]
    GetStdHandle.argtypes = [DWORD]
    GetStdHandle.restype = HANDLE
    
    GetConsoleScreenBufferInfo = windll.kernel32["GetConsoleScreenBufferInfo"]
    GetConsoleScreenBufferInfo.argtypes = [HANDLE, POINTER(CONSOLE_SCREEN_BUFFER_INFO)]
    GetConsoleScreenBufferInfo.restype = BOOL
    
    SetConsoleTextAttribute = windll.kernel32["SetConsoleTextAttribute"]
    SetConsoleTextAttribute.argtypes = [HANDLE, WORD]
    SetConsoleTextAttribute.restype = BOOL
    
    try:
        _win_std_handle = GetStdHandle(STD_OUTPUT_HANDLE)
        if _win_std_handle == 0:
            raise OSError("GetStdHandle failed")
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        if not GetConsoleScreenBufferInfo(_win_std_handle, byref(csbi)):
            raise OSError("GetConsoleScreenBufferInfo failed")
        _win_orig_attrs = csbi.attributes
        _win_curr_attrs = csbi.attributes
    except OSError:
        def _win_console_color(fg = None, bg = None):
            return 0, 0
    else:
        def _win_console_color(fg = None, bg = None):
            global _win_curr_attrs
            prev = _win_curr_attrs
            if fg is not None:
                _win_curr_attrs = (_win_curr_attrs & 0xFFF0) | fg
            if bg is not None:
                _win_curr_attrs = (_win_curr_attrs & 0xFF0F) | (bg << 4)
            SetConsoleTextAttribute(_win_std_handle, _win_curr_attrs)
            return prev & 0xF, (prev >> 4) & 0xF
else:
    def _win_console_color(fg = None, bg = None):
        return 0, 0


class WindowsStyler(BaseStyler):
    COLOR_MAP = dict(
        black = 0,
        blue = 1,
        green = 2,
        cyan = 3,
        red = 4,
        magenta = 5,
        yellow = 6,
        white = 7,
        grey = 8,
        bold_blue = 9,
        bold_green = 10,
        bold_cyan = 11,
        bold_red = 12,
        bold_magenta = 13,
        bold_yellow = 14,
        bold_white = 15,
    )
        
    def __init__(self, fileobj = sys.stdout):
        if fileobj.name not in ("<stdout>", "<stderr>"):
            raise IOError("Only stdout/stderr are supported")
        BaseStyler.__init__(self, fileobj)
    
    @contextmanager
    def colored(self, fg = None, bg = None):
        if fg:
            fg = self.COLOR_MAP.get(fg.strip().lower().replace(" ", "_").replace("-", "_"), None)
        if bg:
            bg = self.COLOR_MAP.get(bg.strip().lower().replace(" ", "_").replace("-", "_"), None)

        ofg, obg = _win_console_color(fg, bg)
        yield
        _win_console_color(ofg, obg)


if not sys.stdout.isatty():
    styler = BaseStyler()
elif sys.platform == "win32":
    styler = WindowsStyler()
else:
    styler = ANSIStyler()


class Styled(object):
    __slots__ = ["value", "fg", "bg"]
    def __init__(self, value, fg, bg):
        self.value = value
        self.fg = fg
        self.bg = bg
    def __str__(self):
        return str(self.value)
    def __format__(self, spec):
        return format(self.value, spec)


class StyleFormatter(Formatter):
    def __init__(self, styler):
        Formatter.__init__(self)
        self.styler = styler
    
    def get_value(self, key, args, kwds):
        if not isinstance(key, str) or "#" not in key:
            return Formatter.get_value(self, key, args, kwds)

        key, style = key.split("#")
        key = key.strip()
        if key.isdigit():
            key = int(key.strip())
            val = Formatter.get_value(self, key, args, kwds)
        elif key[0] == key[-1] == '"' or key[0] == key[-1] == "'":
            val = key[1:-1]
        else:
            val = Formatter.get_value(self, key, args, kwds)
        if "," in style:
            fg, bg = style.split(",")
        else:
            fg, bg = style, ""
        return Styled(val, fg.strip(), bg.strip())
    
    def _vformat(self, format_string, args, kwargs, used_args, recursion_depth):
        if recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')
        
        for literal_text, field_name, format_spec, conversion in self.parse(format_string):
            if literal_text:
                self.styler.write(literal_text)
            if field_name is not None:
                obj, arg_used = self.get_field(field_name, args, kwargs)
                used_args.add(arg_used)
                obj = self.convert_field(obj, conversion)
                format_spec = Formatter._vformat(self, format_spec, args, kwargs, used_args, recursion_depth-1)
                text = self.format_field(obj, format_spec)
                if isinstance(obj, Styled):
                    with self.styler.colored(obj.fg, obj.bg):
                        self.styler.write(text)
                else:
                    self.styler.write(text)
        return ""

style_formatter = StyleFormatter(styler)


if __name__ == "__main__":
    s = ANSIStyler()
    with s.colored("bold red", "white"):
        s.write("hello")
    s.write("moshe\n")

    w = WindowsStyler()
    with w.colored("bold red", "white"):
        w.write("hello")
    w.write("moshe\n")
    
    style_formatter.format("errno is {0 #CYAN,DARK_BLUE:10} and i like {'bananas' # YELLOW}\n", 5)











