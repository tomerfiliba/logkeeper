import sys
from contextlib import contextmanager


class BaseConsole(object):
    def move(self, x, y):
        pass
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
    WHITE   = 0
    INTENSE = 0
    
    def color(self, fg = None, bg = None):
        return None, None
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
            self._curr_fg = None
            self._curr_bg = None
    
        def move(self, x, y):
            self.fileobj.write("\x1b[%s;%sH" % (y, x))
        def color(self, fg = None, bg = None):
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

if not sys.stdout.isatty():
    console = FakeConsole()
elif sys.platform == "win32":
    console = WindowsConsole()
else:
    console = AnsiConsole()


class Styled(object):
    def __init__(self, *contents):
        self.contents = contents
    def __str__(self):
        return "".join(str(cont) for cont in self.contents)
    def write(self):
        for cont in self.contents:
            if isinstance(cont, Styled):
                cont.write()
            else:
                console.write(cont)
    def __add__(self, other):
        return Styled(self, other)
    def __radd__(self, other):
        return Styled(other, self)
#    def __mod__(self, other):
#        pass

class Colored(Styled):
    FG = None
    BG = None
    def __init__(self, *contents):
        Styled.__init__(self, *contents)
    def write(self):
        with console.colored(self.FG, self.BG):
            Styled.write(self)

class Red(Colored):
    FG = console.RED | console.INTENSE
class Green(Colored):
    FG = console.GREEN | console.INTENSE
class Blue(Colored):
    FG = console.BLUE | console.INTENSE



x = Red("hello") + " wor" + Green("ld\n")
x.write()





