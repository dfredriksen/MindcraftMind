import subprocess_maximize as subprocess, time, pyautogui
from Inputs import press_key, release_key, mouse_move_to, mouse_down, mouse_up
from WindowMgr import WindowMgr
from Actions import Actions

class Mind():
  proc = None
  resolution = None
  window = None
  actions = None

  def __del__(self):
    if self.proc != None:
      self.proc.kill()

  def __init__(self):
    print('Detecting resolution...')
    self.resolution = pyautogui.size()
    self.window = WindowMgr()
    print(self.resolution)

  def focus_minecraft_window(self):
    self.window.find_window_wildcard('Minecraft 1*')
    self.window.set_foreground()

  def start_launcher(self, path):
    self.proc = subprocess.Popen(path, show='maximize')

  def play_minecraft(self):
    button_coordinates = self.wait_poll(2, self.find_button, ['assets\\play_button.png', 'Play'])
    pyautogui.click(button_coordinates)
    print('Waiting for Minecraft to launch...')
    time.sleep(30)
    print('Clicking expected location of Multiplayer button')
    pyautogui.click([self.resolution[0] / 2, self.resolution[1] / 2 + 40])
    time.sleep(3)
    x = self.resolution[0] * 0.24
    y = self.resolution[1] * 0.19
    print('Clicking server play button')
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
    print('Looking for ' + button_name + ' button...')
    button_coordinates = pyautogui.locateCenterOnScreen(button, confidence=conf)
    result = button_coordinates != None
    print('Found: ' + str(result))
    return [result, button_coordinates]

  def key_press(self, key, delay=0.5):
    press_key(key)
    time.sleep(delay)
    release_key(key)
  
  def mouse_click(self, x, y, button='left', delay=0.2):
    mouse_down(x, y, button)
    time.sleep(delay)
    mouse_up(x,y, button)
  
  def mouse_down(self, x, y, button='left'):
    mouse_down(x, y, button)
 
  def mouse_up(self, x, y, button='left'):
    mouse_up(x,y,button)
  
  def rotate(self, x, y):
    mouse_move_to(x, y)

  def enumerate_actions(self):
    actions = Actions()
    self.actions = actions.enumerate_actions()