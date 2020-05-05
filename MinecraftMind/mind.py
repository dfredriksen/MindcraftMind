import subprocess_maximize as subprocess, os, time
import win32gui, win32api, pyautogui
import numpy as np
from PIL import Image
from config import AWS_ACCESS_KEY, ACTION_STATEPATH, AWS_SECRET_KEY
from config import S3_BUCKET_NAME, SCREENSHOT_PATH, DONE_STATEPATH
from config import RESIZE_SIZE,  EPS_START, EPS_END, EPS_DECAY
from config import CLEAN_THREADS, MINECRAFT_LAUNCHER_PATH, LEARNING_HOST
from config import DEVICE
import torch
import math
from itertools import count
import random
from mind_dqn import DQN
from mind_actions import ActionExecutor, Actions, process_state_actions
from mind_cnn_done import CNNDone, detect_is_done
from mind_windows import WindowMgr
from mind_input import mouse_move_to, mouse_down, mouse_up, press_key, release_key
from mind_memory import Memory
from mind_policy import get_policy_version, download_policy, PolicyLoader
import requests
from pickle import loads

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
    self.policy_version = 1
    self.logger = logger
    self.detect_resolution()
    self.device = DEVICE
    self.window = WindowMgr()
    self.initialize_done_detector()
    self.initialize_actions()
    self.trial = time.time()
    self.initialize_policy_net()    
    self.memory_threads = []
    self.state = None
    self.policy_loader = None

  def initialize_policy_net(self):
    self.output('Initializing Policy DQN...')
    version = get_policy_version()
    self.policy_net = DQN(self.sight_height, self.sight_width, self.n_actions).to(self.device)
    if int(version) > 1 and int(version) != self.policy_version:
      self.output("Loading policy version #" + version)
      download_policy(version)
      self.policy_net.load_state_dict(torch.load(ACTION_STATEPATH))
      self.policy_net.eval()
      self.policy_version = version

  def initialize_actions(self):
    self.output('Initializing Available Actions...')
    self.enumerate_actions()    
    n_actions = 0
    for actions in self.action_spaces:
      n_actions = n_actions + actions
    self.n_actions = n_actions

  def initialize_done_detector(self):
    self.output('Initializing Done Detector...')
    self.done_model = CNNDone()
    self.output('Loading Done Detector Model Params')
    self.done_model.load_state_dict(torch.load(DONE_STATEPATH))
    
  def detect_resolution(self):
    self.output('Detecting resolution...')
    self.resolution = pyautogui.size()
    assert self.resolution[0] == 800 and self.resolution[1] == 600, "Only 800 x 600 resolution is supported"
    self.sight_width = int(RESIZE_SIZE * (self.resolution[0]/self.resolution[1]))
    self.sight_height = RESIZE_SIZE
    self.output('Resolution: ' + str(self.resolution[0]) + ' x ' + str(self.resolution[1]))
    self.output('Resized Resolution: ' + str(self.sight_width) + ' x ' + str(self.sight_height))

  def select_action(self, state, steps_done):
    sample = random.random()
    eps_threshold = EPS_END + (EPS_START - EPS_END) * \
        math.exp(-1. * steps_done / EPS_DECAY)
    if sample > eps_threshold:
        with torch.no_grad():
          # t.max(1) will return largest column value of each row.
          # second column on max result is index of where max element was
          # found, so we pick action with the larger expecte,d reward.
          #return policy_net(state).max(1)[1].view(1, 1)
          output = self.policy_net(state)
          return process_state_actions(output, self.action_spaces)
    else:
        random_actions = []
        for actions in self.action_spaces:
          random_actions.append(random.randrange(actions))
        return torch.tensor([random_actions], device=self.device, dtype=torch.long)

  def learning_loop(self):
    i_episode = -1
    while True:
        i_episode = i_episode + 1
        self.output('Starting episode ' + str(i_episode) + '...')
        self.respawn()
        last_screen = self.get_screen()
        current_screen = self.get_screen()
        state = current_screen - last_screen
        steps_done = 0
        for t in count():
            # Select and perform an action
            action = self.select_action(state, steps_done)
            action_list = action.numpy()[0]
            self.output(action_list)
            environment, reward, done, filename = self.step(action_list)
            steps_done = steps_done + 1
            self.output('Step: ' + str(steps_done))
            # Observe new state
            last_screen = current_screen
            current_screen = self.get_screen()
            if not done:
                next_state = current_screen - last_screen
            else:
                next_state = None
                
            memory = Memory(environment, filename, done, reward, self.trial, i_episode, steps_done, state, next_state, action_list, self.inventory, self.policy_version, self.memory_threads)
            memory.start()
            self.output("Starting memory thread:" + memory.name)
            self.memory_threads.append(memory)
            state = next_state
            if done:
                self.output('Agent has died...')
                self.clean_memory_threads()
                self.output('Waiting for learning threads to complete...')
                self.join_memory_threads()
                self.initialize_policy_net()
                break
            
            if steps_done % CLEAN_THREADS == 0:
                self.clean_memory_threads()

            if self.policy_loader == None:
              self.policy_loader = PolicyLoader(self.sight_height, self.sight_width, self.n_actions)
              self.policy_loader.start()

            if self.policy_loader.loaded:
              if self.policy_loader.new_net != None:
                self.policy_net = self.policy_loader.new_net
                self.policy_version = self.policy_loader.new_version
              self.policy_loader = None

  def join_memory_threads(self):
    for memory_thread in self.memory_threads:
      if memory_thread.is_alive():
        self.output("Waiting for thread " + memory_thread.name)
        memory_thread.join()
    self.output("All learning threads processed.")
    self.memory_threads = []

  def clean_memory_threads(self):
    new_memory_threads = []
    for memory_thread in self.memory_threads:
      if memory_thread.is_alive():
        new_memory_threads.append(memory_thread)
    self.memory_threads = new_memory_threads

  def render(self):
    if self.state is None:
      state = np.array(Image.new('RGBA',(self.sight_width,self.sight_height), (255, 255, 255, 255)))
    else:
      state = np.array(self.state)  
    return state

  def get_screen(self):
    # Transpose it into torch order (CHW).
    screen = self.render().transpose((2, 0, 1))
    screen = np.ascontiguousarray(screen, dtype=np.float32) / 255
    screen = torch.from_numpy(screen)
    # Resize, and add a batch dimension (BCHW)
    result = screen.unsqueeze(0).to(self.device)
    return result
  
  def step(self, action):
    threads = []
    for index, action_item in enumerate(action):
      action_thread = self.perform_action(self.actions[index][action_item])
      threads.append(action_thread)
    
    for thread in threads:
      thread.join()

    im = self.get_state()
    r_im = self.done_model.process_image(im)
    self.state = r_im
    c_im = self.done_model.crop_image(r_im)
    done = detect_is_done(c_im, self.done_model)
    reward = 0
    if done:
      reward = -100 
    return self.state, reward, done, im.filename

  def get_state(self):
    im = None
    filename = ""
    files = []
    while im == None:
      self.look()
      while len(files) == 0:
        files = os.listdir(SCREENSHOT_PATH)
        if(len(files) > 0):
          files.sort(reverse=True)
          filename = files[0]
          state = os.path.join(SCREENSHOT_PATH, filename)
      retries = 0
      while im == None:
        try:
          im = Image.open(state)
        except: 
          retries = retries + 1
          time.sleep(0.1)
          if retries > 100:
            break
    return im

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
    ex = self.resolution[0] < cx
    ey = self.resolution[1] < cy
    if(not self.inventory or not (ex and ey )):
      mouse_move_to(x, y)

  def no_op(self, delay = 0):
    time.sleep(delay)
  
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
    available_actions, action_space = actions.enumerate_actions()
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
    action_thread = ActionExecutor(action, self)
    action_thread.start()
    return action_thread
