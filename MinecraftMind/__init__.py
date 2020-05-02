import subprocess_maximize as subprocess, os, ctypes, time
import win32gui, win32api, win32con, pyautogui, re
import numpy as np
from PIL import Image
from threading import Thread
import boto3
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_LOCATION
from config import S3_BUCKET_NAME, SCREENSHOT_PATH, DONE_STATEPATH, RESIZE_SIZE
from cnn_done import CNNDone, detect_is_done
import torch

class Mind():
  proc = None
  resolution = None
  window = None
  actions = None
  logger = None
  verbose_mode = 'print' #modes: log, print, all, none
  key_active = {}
  mouse_active = {}
  mouse_x = 0
  mouse_y = 0
  inventory = False

  def __del__(self):
    if self.proc != None:
      self.proc.kill()

  def __init__(self, verbose = 'print', logger=None):
    self.verbose_mode = verbose
    self.logger = logger
    self.output('Detecting resolution...')
    self.resolution = pyautogui.size()
    self.output('Resolution: ' + str(self.resolution[0]) + ' x ' + str(self.resolution[1]))
    self.window = WindowMgr()
    self.enumerate_actions()
    pyautogui.FAILSAFE = False
    
  def focus_minecraft_window(self, title='Minecraft 1*'):
    self.output('Focus window matching: ' + title)
    self.window.find_window_wildcard(title)
    self.window.set_foreground()

  def start_launcher(self, path):
    self.output('Starting Minecraft launcher at: ' + path)
    self.proc = subprocess.Popen(path, show='maximize')
    self.output('Waiting for Minecraft to launch...')
    button_coordinates = self.wait_poll(2, self.find_button, ['assets\\\\\\\\play_button.png', 'Play'])
    return button_coordinates

  def play_minecraft_multiplayer(self, button_coordinates, delay=30):
    self.output('Clicking play...')
    pyautogui.click(button_coordinates)
    self.output('Waiting ' + str(delay) + ' seconds for Minecraft to load...')
    time.sleep(delay)
    self.output('Clicking expected location of Multiplayer button')
    pyautogui.click([self.resolution[0] / 2, self.resolution[1] / 2 + 40])
    time.sleep(3)
    x = self.resolution[0] * 0.24
    y = self.resolution[1] * 0.19
    self.output('Clicking server play button')
    pyautogui.moveTo([x,y])
    time.sleep(1)
    pyautogui.click()

  def wait_poll(self, delay, callback, data, epochs = 10):
    for _ in range(epochs):
      result, value = callback(*data)
      if result:
        return value
      time.sleep(delay)
    return None

  def find_button(self, button, button_name, conf=0.99):
    self.output('Looking for ' + button_name + ' button...')
    button_coordinates = pyautogui.locateCenterOnScreen(os.path.join(os.path.dirname(__file__), button), confidence=conf)
    result = button_coordinates != None
    self.output('Found: ' + str(result))
    return [result, button_coordinates]

  def toggle_inventory(self, key, delay=0.5):
    self.mouse_x = 0
    self.mouse_y = 0  
    self.key_press(key, delay)
    self.inventory = not self.inventory
    self.output('Inventory toggled: ' + str(self.inventory))
    win32api.SetCursorPos((int(self.resolution[0]/2), int(self.resolution[1]/2)))

  def key_press(self, key, delay=0.4):
    self.output('Initiating keypress sequence: ' + str(key))
    press_key(key)
    time.sleep(delay)
    release_key(key)


  def key_down(self, key):
    self.output('Press key: ' + str(key))
    press_key(key)
    

  def key_up(self, key):
    self.output('Release key: ' + str(key))
    release_key(key)


  def key_toggle(self, key):
    if key in self.key_active.keys() and self.key_active[key]:
      self.output('Release key: ' + str(key))
      self.key_up(key)
      self.key_active[key] = False
    else:
      self.output('Press key: ' + str(key))
      self.key_down(key)
      self.key_active[key] = True


  def mouse_toggle(self, button):
    if button in self.mouse_active.keys() and self.mouse_active[button]:
      self.output('Mouse up (' + button  + ') at: (0, 0)')
      self.mouse_up(0, 0, button)
      self.mouse_active[button] = False
    else:
      self.output('Mouse down (' + button  + ') at: (0, 0)')
      self.mouse_down(0, 0, button)
      self.mouse_active[button] = True    

  def mouse_click(self, x, y, button='left', delay=0.1):
    self.output('Mouse click (' + button  + ') at: (' + str(x) + ', ' + str(y) + ')')
    mouse_down(x, y, button)
    time.sleep(delay)
    mouse_up(x,y, button)


  def mouse_down(self, x, y, button='left'):
    self.output('Mouse down (' + button  + ') at: (' + str(x) + ', ' + str(y) + ')')
    mouse_down(x, y, button)


  def mouse_up(self, x, y, button='left'):
    self.output('Mouse up (' + button  + ') at: (' + str(x) + ', ' + str(y) + ')')
    mouse_up(x, y, button)


  def look(self, delay=0.1):
    self.output('Looking (Taking screenshot)...')
    self.key_press(Actions.screenshot, delay)


  def rotate(self, x, y):
    self.output('Move to: (' + str(x) + ', ' + str(y) + ')')
    cx, cy = win32gui.GetCursorPos()
    xx = cx+x
    yy = cy+y
    ex = self.resolution[0] < cx
    ey = self.resolution[1] < cy
    if(not self.inventory or not (ex and ey )):
      mouse_move_to(x, y)

  def no_op(self, delay = 0):
    time.sleep(delay)


  def is_dead(self, path):
    wait_count = 0
    im = None
    while im is None:
      wait_count = wait_count + 1    
      try:
        im = Image.open(path)
      except:
        time.sleep(0.01)
        if(wait_count > 100):
          break
  
    self.output('Checking if agent died...')
    x = int(self.resolution[0] * 0.390625)
    y = int(self.resolution[1] * 0.203703)
    x2 = int(self.resolution[0] * 0.598958)
    y2 = int(self.resolution[1] * 0.305555)
    width = x2 - x
    height = y2 - y
    im2 = im.crop((x, y, x2, y2))
    im2 = im2.convert("1", dither=Image.NONE).resize((int(width / 2), int(height / 2)))
    self.output(text)
    died = text.find('died') > -1
    self.output('Died: ' + str(died))
    if died and not self.inventory:
        self.mouse_x = 0
        self.mouse_y = 0
    return died
  

  def respawn(self):
    self.output('Respawning....')
    self.mouse_active['mode'] = 'game'
    self.inventory = False
    self.focus_minecraft_window()
    tx = int((self.resolution[0]/2))
    ty = int(self.resolution[1] * 0.55)
    self.release_keys_and_mouse()
    self.inventory = False
    win32api.SetCursorPos((tx, ty))
    self.mouse_click(tx, ty)

 
  def release_keys_and_mouse(self):
    for index,key_key in enumerate(self.key_active):
      if(self.key_active[key_key]):
        self.key_up(key_key)
        self.key_active[key_key] = False
    for index,button_key in enumerate(self.mouse_active):
      if(self.mouse_active[button_key] and button_key != 'mode'):
        self.mouse_up(0, 0, button_key)
        self.mouse_active[button_key] = False  
    

  def enumerate_actions(self):
    actions = Actions()
    available_actions, action_space = actions.enumerate_actions(self)
    self.actions = available_actions
    self.action_spaces = action_space


  def output(self, message):
    timestamp = time.ctime(time.time())
    if (self.verbose_mode == 'print' or self.verbose_mode == 'all'):
      print(str(timestamp) + ': ' + str(message))
    if (self.verbose_mode == 'log' or self.verbose_mode == 'all'):
      self.logger.debug(str(timestamp) + ': ' + message)


  def perform_action(self, action):
    self.output('Performing action: ' + action["name"])
    action_thread = ActionExecutor(action)
    action_thread.start()
    return action_thread


class ActionExecutor(Thread):

  def __init__(self, action):
    Thread.__init__(self)
    self.action = action

  def run(self):
    self.action["method"](*self.action["arguments"])


class Actions():

  forward = 0x11
  left = 0x1E
  right = 0x20
  back = 0x1F
  drop = 0x10
  jump = 0x39
  inventory = 0x12
  slot1 = 0x02
  slot2 = 0x03
  slot3 = 0x04
  slot4 = 0x05
  slot5 = 0x06
  slot6 = 0x07
  slot7 = 0x08
  slot8 = 0x09
  slot9 = 0x0A
  run_swim = 0x1D
  stealth = 0x2A
  screenshot = 0x3C

  def __init__(self):
    return None

  def enumerate_actions(self, mind):
    action_list = [
      [
        {
        "name": 'move forward',
        "method": mind.key_press,
        "arguments": [self.forward],
        },{ 
        "name": 'strafe left',
        "method": mind.key_press,
        "arguments": [self.left],
        },{
        "name": 'strafe right',
        "method": mind.key_press,
        "arguments": [self.right],
        },{
        "name": 'backpedal',
        "method": mind.key_press,
        "arguments": [self.back],
        }
      ], 
      [
        {
        "name": 'jump',
        "method": mind.key_press,
        "arguments": [self.jump],
        }], 
        [{
        "name": 'run/swim',
        "method": mind.key_toggle,
        "arguments": [self.run_swim],
        }, {
        "name": 'stealth/dive',
        "method": mind.key_toggle,
        "arguments": [self.stealth],
        }
      ],
      [
        {
        "name": 'left click',
        "method": mind.mouse_click,
        "arguments": [0, 0, 'left'],
        },{
        "name": 'right click',
        "method": mind.mouse_click,
        "arguments": [0, 0, 'right'],
        },{
        "name": 'left mouse',
        "method": mind.mouse_toggle,
        "arguments": ['left'],
        },{
        "name": 'right mouse',
        "method": mind.mouse_toggle,
        "arguments": ['right'],
        }
      ],
      [
        {
        "name": 'rotate right',
        "method": mind.rotate,
        "arguments": [80, 0]
        }, {
        "name": 'rotate left',
        "method": mind.rotate,
        "arguments": [-80, 0]
        }, {
        "name": 'rotate up',
        "method": mind.rotate,
        "arguments": [0, -40]
        }, {
        "name": 'rotate down',
        "method": mind.rotate,
        "arguments": [0, 40]
        }, {
        "name": 'rotate right-up',
        "method": mind.rotate,
        "arguments": [80, -40]
        }, {
        "name": 'rotate right-down',
        "method": mind.rotate,
        "arguments": [80, 40]
        }, {
        "name": 'rotate left-up',
        "method": mind.rotate,
        "arguments": [-80, -40]
        }, {
        "name": 'rotate left-down',
        "method": mind.rotate,
        "arguments": [-80, -40]
        }
      ],
      [
        {
        "name": 'drop',
        "method": mind.key_press,
        "arguments": [self.drop],
        },
        {
        "name": 'inventory',
        "method": mind.toggle_inventory,
        "arguments": [self.inventory],
        }, {
        "name": 'wield hotbar1',
        "method": mind.key_press,
        "arguments": [self.slot1],
        }, {
        "name": 'wield hotbar2',
        "method": mind.key_press,
        "arguments": [self.slot2],
        }, {
        "name": 'wield hotbar3',
        "method": mind.key_press,
        "arguments": [self.slot3],
        }, {
        "name": 'wield hotbar4',
        "method": mind.key_press,
        "arguments": [self.slot4],
        }, {
        "name": 'wield hotbar5',
        "method": mind.key_press,
        "arguments": [self.slot5],
        }, {
        "name": 'wield hotbar6',
        "method": mind.key_press,
        "arguments": [self.slot6],
        }, {
        "name": 'wield hotbar7',
        "method": mind.key_press,
        "arguments": [self.slot7],
        }, {
        "name": 'wield hotbar8',
        "method": mind.key_press,
        "arguments": [self.slot8],
        }, {
        "name": 'wield hotbar9',
        "method": mind.key_press,
        "arguments": [self.slot9],
        }
      ]
    ]

    action_spaces = []
    actions = []
    for group in action_list:
      group.append({
        "name": 'NO OP',
        "method": mind.no_op,
        "arguments": [1],
      })
      action_spaces.append(len(group))
      actions.append(group)

    return actions, action_spaces

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


class WindowMgr():
    """Encapsulates some calls to the winapi for window management"""

    def __init__ (self):
        """Constructor"""
        self._handle = None
        
    def __about__(self):
      """This is not my implementation. I found it somewhere on the
      internet, presumably on StackOverflow.com and extended it by
      the last method that returns the hwnd handle."""
      pass

    def find_window(self, class_name, window_name=None):
        """find a window by its class_name"""
        self._handle = win32gui.FindWindow(class_name, window_name)

    def _window_enum_callback(self, hwnd, wildcard):
        """Pass to win32gui.EnumWindows() to check all the opened windows"""
        if re.match(wildcard, str(win32gui.GetWindowText(hwnd))) is not None:
            self._handle = hwnd

    def find_window_wildcard(self, wildcard):
        """find a window whose title matches the wildcard regex"""
        self._handle = None
        win32gui.EnumWindows(self._window_enum_callback, wildcard)

    def set_foreground(self):
        """put the window in the foreground"""
        win32gui.SetForegroundWindow(self._handle)

    def get_hwnd(self):
        """return hwnd for further use"""
        return self._handle

#timestamp_start = time.time()
#s3 = boto3.client(
#  "s3",
#  aws_access_key_id = AWS_ACCESS_KEY,
#  aws_secret_access_key = AWS_SECRET_KEY
#)

#bucket_resource = s3

#bucket_resource.upload_file(
#  Bucket = S3_BUCKET_NAME,
#  Filename = os.path.join(SCREENSHOT_PATH, '2020-05-01_11.59.56.png'),
#  Key='trial1.png'
#)

#timestamp_end = time.time()

#print(str(timestamp_start - timestamp_end) + ' unix timestamp ticks')

#print(time.time())
#print(time.time())

mcmind = Mind()
done_model = CNNDone(int(RESIZE_SIZE * (600/800)), RESIZE_SIZE)
done_model.load_state_dict(torch.load(DONE_STATEPATH))
while True:
  mcmind.look()
  files = []
  while len(files) == 0:
    files = os.listdir(SCREENSHOT_PATH) #images = self.poll_for_screenshot(self.screenshot_path)
    if(len(files) > 0):
      files.sort(reverse=True)
      state = os.path.join(SCREENSHOT_PATH, files[0])
  im = None
  retries = 0
  while im == None:
    try:
      im = Image.open(state)
    except: 
      retries = retries + 1
      time.sleep(0.05)
      if retries > 100:
        break
  if im == None:
    continue

  r_im = done_model.process_image(im)
  c_im = done_model.crop_image(im, r_im)
  done = detect_is_done(c_im,done_model)
  print('Done: ' + str(done))
  quit()
  if done:
    break
  time.sleep(1)

print('Complete')