import sys


class BaseConsole(object):
    def move(self, x, y):
        pass
    def color(self, fg = None, bg = None):
        pass
    def clear(self):
        pass
    def reset(self):
        pass
    def write(self, text):
        pass
    def writeln(self, text):
        self.write(text + "\n")

class FakeConsole(BaseConsole):
    def write(self, text):
        sys.stdout.write(text)


if sys.platform == "win32":
    from ctypes import byref
    from ctypes import windll, Structure, POINTER, c_char
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
        GREY    = 7
        INTENSE = 8
        
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
            if fg is not None:
                self._curr_attrs = (self._curr_attrs & 0xFFF0) | fg
            if bg is not None:
                self._curr_attrs = (self._curr_attrs & 0xFF0F) | (bg << 4)
            SetConsoleTextAttribute(self._handle, self._curr_attrs)
        
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

else:
    class AnsiConsole(BaseConsole):
        BLACK   = 0
        RED     = 1
        GREEN   = 2
        YELLOW  = 3
        BLUE    = 4
        MAGENTA = 5
        CYAN    = 6
        WHITE   = 7
        INTENSE = 8
        
        def __init__(self, fileobj = sys.stdout):
            self.fileobj = fileobj
    
        def move(self, x, y):
            self.fileobj.write("\x1b[%s;%sH" % (y, x))
        def color(self, fg = None, bg = None):
            codes = []
            if fg is not None:
                if fg & self.INTENSE:
                    codes.append("1")
                codes.append("3%d" % (fg & 0x7,))
            if bg is not None:
                codes.append("4%d" % (bg & 0x7,))
            self.fileobj.write("\x1b[%sm" % (";".join(codes)))
        
        def clear(self):
            self.fileobj.write("\x1b[2J\x1b[1;1H")
        def reset(self):
            self.fileobj.write("\x1b[0m")
        def write(self, text):
            self.fileobj.write(text)    

if not sys.stdout.isatty():
    console = FakeConsole()
elif sys.platform == "win32":
    console = WindowsConsole()
else:
    console = AnsiConsole()

class Style(object):
    def __init__(self, fg = None, bg = None):
        self.fg = fg
        self.bg = bg
    def __enter__(self):
        console.color(self.fg, self.bg)
    def __exit__(self, t, v, tb):
        pass

class Intense(Style):
    def __or__(self, other):
        return Style(other.fg | console.INTENSE)
    __ror__ = __or__

INTENSE = Intense()
RED = Style(fg = console.RED)
BG_GREEN = Style(bg = console.GREEN)

with BG_GREEN, RED | INTENSE:
    console.writeln("hello")














