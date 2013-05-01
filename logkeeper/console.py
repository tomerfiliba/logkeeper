import sys
from contextlib import contextmanager
from string import Formatter


class BaseConsole(object):
    COLOR_MAP = {}
    def move(self, x, y):
        pass
    
    def _color_from_name(self, name):
        return self.COLOR_MAP.get(name.strip().lower().replace("-", "_"), None)
    
    def color(self, fg = None, bg = None):
        pass
    @contextmanager
    def colored(self, fg = None, bg = None):
        ofg, obg = self.color(fg, bg)
        yield
        self.color(ofg, obg)
    def clear(self):
        pass
    def reset(self):
        pass
    def write(self, text):
        pass
    def writeln(self, text):
        self.write(text + "\n")

class FakeConsole(BaseConsole):
    BLACK   = 0
    RED     = 0
    GREEN   = 0
    YELLOW  = 0
    BLUE    = 0
    MAGENTA = 0
    CYAN    = 0
    WHITE = GREY = 0
    INTENSE = 0
    
    def color(self, fg = None, bg = None):
        return None, None
    def write(self, text):
        sys.stdout.write(text)

class AnsiConsole(BaseConsole):
    BLACK   = 0
    RED     = 1
    GREEN   = 2
    YELLOW  = 3
    BLUE    = 4
    MAGENTA = 5
    CYAN    = 6
    WHITE = GREY = 7
    INTENSE = 8

    COLOR_MAP = dict(
        black = BLACK,
        dark_blue = BLUE,
        dark_green = GREEN,
        dark_cyan = CYAN,
        dark_red = RED,
        magenta = MAGENTA,
        gold = YELLOW,
        dark_yellow = YELLOW,
        grey = GREY,
        dark_grey = BLACK | INTENSE,
        blue = BLUE | INTENSE,
        green = GREEN | INTENSE,
        cyan = CYAN | INTENSE,
        red = RED | INTENSE,
        purple = MAGENTA | INTENSE,
        yellow = YELLOW | INTENSE,
        white = GREY | INTENSE,
    )
    
    def __init__(self, fileobj = sys.stdout):
        self.fileobj = fileobj
        self._curr_fg = None
        self._curr_bg = None

    def move(self, x, y):
        self.fileobj.write("\x1b[%s;%sH" % (y, x))
    def color(self, fg = None, bg = None):
        if isinstance(fg, str):
            fg = self._color_from_name(fg)
        if isinstance(bg, str):
            bg = self._color_from_name(bg)
        ofg = self._curr_fg
        obg = self._curr_bg
        codes = []
        if fg is not None:
            if fg & self.INTENSE:
                codes.append("1")
            codes.append("3%d" % (fg & 0x7,))
            self._curr_fg = fg
        if bg is not None:
            codes.append("4%d" % (bg & 0x7,))
            self._curr_bg = bg
        self.fileobj.write("\x1b[%sm" % (";".join(codes)))
        return ofg, obg
    
    def clear(self):
        self.fileobj.write("\x1b[2J\x1b[1;1H")
    def reset(self):
        self.fileobj.write("\x1b[0m")
    def write(self, text):
        self.fileobj.write(text)    


if sys.platform == "win32":
    from ctypes import windll, Structure, POINTER, c_char, byref
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
    
    GetLastError = windll.kernel32["GetLastError"]
    GetLastError.argtypes = []
    GetLastError.restype = DWORD
    
    GetStdHandle = windll.kernel32["GetStdHandle"]
    GetStdHandle.argtypes = [DWORD]
    GetStdHandle.restype = HANDLE
    
    GetConsoleScreenBufferInfo = windll.kernel32["GetConsoleScreenBufferInfo"]
    GetConsoleScreenBufferInfo.argtypes = [HANDLE, POINTER(CONSOLE_SCREEN_BUFFER_INFO)]
    GetConsoleScreenBufferInfo.restype = BOOL
    
    SetConsoleTextAttribute = windll.kernel32["SetConsoleTextAttribute"]
    SetConsoleTextAttribute.argtypes = [HANDLE, WORD]
    SetConsoleTextAttribute.restype = BOOL
    
    SetConsoleCursorPosition = windll.kernel32["SetConsoleCursorPosition"]
    SetConsoleCursorPosition.argtypes = [HANDLE, COORD]
    SetConsoleCursorPosition.restype = BOOL
     
    FillConsoleOutputCharacter = windll.kernel32["FillConsoleOutputCharacterA"]
    FillConsoleOutputCharacter.argtypes = [HANDLE, c_char, DWORD, COORD, POINTER(DWORD)]
    FillConsoleOutputCharacter.restype = BOOL
    
    FillConsoleOutputAttribute = windll.kernel32["FillConsoleOutputAttribute"]
    FillConsoleOutputAttribute.argtypes = [HANDLE, WORD, DWORD, COORD, POINTER(DWORD)]
    FillConsoleOutputAttribute.restype = BOOL

    class WindowsConsole(BaseConsole):
        BLACK   = 0
        BLUE    = 1
        GREEN   = 2
        CYAN    = 3
        RED     = 4
        MAGENTA = 5
        YELLOW  = 6
        WHITE = GREY = 7
        INTENSE = 8

        COLOR_MAP = dict(
            black = BLACK,
            dark_blue = BLUE,
            dark_green = GREEN,
            dark_cyan = CYAN,
            dark_red = RED,
            magenta = MAGENTA,
            gold = YELLOW,
            dark_yellow = YELLOW,
            grey = GREY,
            dark_grey = BLACK | INTENSE,
            blue = BLUE | INTENSE,
            green = GREEN | INTENSE,
            cyan = CYAN | INTENSE,
            red = RED | INTENSE,
            purple = MAGENTA | INTENSE,
            yellow = YELLOW | INTENSE,
            white = GREY | INTENSE,
        )
        
        def __init__(self):
            self._handle = GetStdHandle(STD_OUTPUT_HANDLE)
            if self._handle == 0:
                raise WindowsError("GetStdHandle failed")
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            if not GetConsoleScreenBufferInfo(self._handle, byref(csbi)):
                raise WindowsError("GetConsoleScreenBufferInfo failed")
            self._orig_attrs = csbi.attributes
            self._curr_attrs = self._orig_attrs
        
        def move(self, x, y):
            SetConsoleCursorPosition(self._handle, COORD(x-1, y-1))
        def color(self, fg = None, bg = None):
            if isinstance(fg, str):
                fg = self._color_from_name(fg)
            if isinstance(bg, str):
                bg = self._color_from_name(bg)
            prev = self._curr_attrs
            if fg is not None:
                self._curr_attrs = (self._curr_attrs & 0xFFF0) | fg
            if bg is not None:
                self._curr_attrs = (self._curr_attrs & 0xFF0F) | (bg << 4)
            SetConsoleTextAttribute(self._handle, self._curr_attrs)
            return prev & 0xF, (prev >> 4) & 0xF
        
        def clear(self):
            csbi = CONSOLE_SCREEN_BUFFER_INFO()
            GetConsoleScreenBufferInfo(self._handle, byref(csbi))
            dwConSize = csbi.size.X * csbi.size.Y
            coordScreen = COORD(0, 0)
            cCharsWritten = DWORD(0)
            FillConsoleOutputCharacter(self._handle, " ", dwConSize, coordScreen, byref(cCharsWritten))
            FillConsoleOutputAttribute(self._handle, self._orig_attrs, dwConSize, coordScreen, byref(cCharsWritten))
            SetConsoleCursorPosition(self._handle, coordScreen)
        
        def reset(self):
            self._curr_attrs = self._orig_attrs
            SetConsoleTextAttribute(self._handle, self._curr_attrs)
        
        def write(self, text):
            sys.stdout.write(text)

if not sys.stdout.isatty():
    console = FakeConsole()
elif sys.platform == "win32":
    try:
        console = WindowsConsole()
    except WindowsError:
        console = FakeConsole()
else:
    console = AnsiConsole()


class Styled(object):
    __slots__ = ["value", "fg", "bg"]
    def __init__(self, value, style):
        self.value = value
        if "," in style:
            self.fg, self.bg = style.split(",")
        else:
            self.fg, self.bg = style, ""
    def __str__(self):
        return str(self.value)
    def __format__(self, spec):
        return format(self.value, spec)

class ConsoleFormatter(Formatter):
    def __init__(self, console):
        Formatter.__init__(self)
        self.console = console
    
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
        return Styled(val, style.strip())
    
    def _vformat(self, format_string, args, kwargs, used_args, recursion_depth):
        if recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')
        
        for literal_text, field_name, format_spec, conversion in self.parse(format_string):
            if literal_text:
                self.console.write(literal_text)
            if field_name is not None:
                obj, arg_used = self.get_field(field_name, args, kwargs)
                used_args.add(arg_used)
                obj = self.convert_field(obj, conversion)
                format_spec = Formatter._vformat(self, format_spec, args, kwargs, used_args, recursion_depth-1)
                text = self.format_field(obj, format_spec)
                if isinstance(obj, Styled):
                    with self.console.colored(obj.fg, obj.bg):
                        self.console.write(text)
                else:
                    self.console.write(text)
        return ""

console_formatter = ConsoleFormatter(console)


if __name__ == "__main__":
    console_formatter.format("errno is {0 #CYAN,DARK_BLUE:10} and i like {'bananas' # YELLOW}", 5)





