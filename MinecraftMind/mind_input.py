import ctypes, win32con, win32api


PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
   _fields_ = [("wVk", ctypes.c_ushort),
               ("wScan", ctypes.c_ushort),
               ("dwFlags", ctypes.c_ulong),
               ("time", ctypes.c_ulong),
               ("dwExtraInfo", PUL)]


class HardwareInput(ctypes.Structure):
   _fields_ = [("uMsg", ctypes.c_ulong),
               ("wParamL", ctypes.c_short),
               ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
   _fields_ = [("dx", ctypes.c_long),
               ("dy", ctypes.c_long),
               ("mouseData", ctypes.c_ulong),
               ("dwFlags", ctypes.c_ulong),
               ("time", ctypes.c_ulong),
               ("dwExtraInfo", PUL)]


class Input_I(ctypes.Union):
   _fields_ = [("ki", KeyBdInput),
               ("mi", MouseInput),
               ("hi", HardwareInput)]


class Input(ctypes.Structure):
   _fields_ = [("type", ctypes.c_ulong),
("ii", Input_I)]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def press_key(key):
  extra = ctypes.c_ulong(0)
  ii_ = Input_I()

  flags = 0x0008

  ii_.ki = KeyBdInput(0, key, flags, 0, ctypes.pointer(extra))
  x = Input(ctypes.c_ulong(1), ii_)
  ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def release_key(key):
  extra = ctypes.c_ulong(0)
  ii_ = Input_I()

  flags = 0x0008 | 0x0002

  ii_.ki = KeyBdInput(0, key, flags, 0, ctypes.pointer(extra))
  x = Input(ctypes.c_ulong(1), ii_)
  ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def cursor_position():
  pt = POINT(0, 0)
  ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
  return [pt.x, pt.y]

def mouse_down(x, y, type='left'):
    if(type == 'left'):
      button = win32con.MOUSEEVENTF_LEFTDOWN
    else:
      button = win32con.MOUSEEVENTF_RIGHTDOWN

    #win32api.SetCursorPos((x, y))
    win32api.mouse_event(button, x, y, 0, 0)
    
def mouse_up(x, y, type='left'):
    if(type == 'left'):
      button = win32con.MOUSEEVENTF_LEFTUP
    else:
      button = win32con.MOUSEEVENTF_RIGHTUP

    #win32api.SetCursorPos((x, y))
    win32api.mouse_event(button, x, y, 0, 0)
    
# Actuals Functions
def mouse_move_to(x, y):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(x, y, 0, 0x0001, 0, ctypes.pointer(extra))

    command = Input(ctypes.c_ulong(0), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))