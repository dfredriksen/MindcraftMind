from threading import Thread
import torch
import numpy as np

def process_state_actions(action_tensor, action_spaces):
    placeholder = action_tensor.numpy()[0]
    action_probabilities = []
    count = 0
    for group, action_items in enumerate(action_spaces):
      action_probabilities.append([])
      for index in range(count, count + action_items):
        action_probabilities[group].append(placeholder[index])
        count = count + 1

    choices = []
    for discrete_action_space in action_probabilities:
      choices.append(np.argmax(discrete_action_space))
    choice_tensor = torch.tensor([choices])  
    return choice_tensor

class ActionExecutor(Thread):

  def __init__(self, action, agent):
    Thread.__init__(self)
    self.action = action
    self.agent = agent

  def run(self):
    action = getattr(self.agent, self.action["method"])
    action(*self.action["arguments"])


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

  def enumerate_actions(self):
    action_list = [
      [
        {
        "name": 'move forward',
        "method": 'key_press',
        "arguments": [self.forward],
        },{ 
        "name": 'strafe left',
        "method": 'key_press',
        "arguments": [self.left],
        },{
        "name": 'strafe right',
        "method": 'key_press',
        "arguments": [self.right],
        },{
        "name": 'backpedal',
        "method": 'key_press',
        "arguments": [self.back],
        }
      ], 
      [
        {
        "name": 'jump',
        "method": 'key_press',
        "arguments": [self.jump],
        }], 
        [{
        "name": 'run/swim',
        "method": 'key_toggle',
        "arguments": [self.run_swim],
        }, {
        "name": 'stealth/dive',
        "method": 'key_toggle',
        "arguments": [self.stealth],
        }
      ],
      [
        {
        "name": 'left click',
        "method": 'mouse_click',
        "arguments": [0, 0, 'left'],
        },{
        "name": 'right click',
        "method": 'mouse_click',
        "arguments": [0, 0, 'right'],
        },{
        "name": 'left mouse',
        "method": 'mouse_toggle',
        "arguments": ['left'],
        },{
        "name": 'right mouse',
        "method": 'mouse_toggle',
        "arguments": ['right'],
        }
      ],
      [
        {
        "name": 'rotate right',
        "method": 'rotate',
        "arguments": [80, 0]
        }, {
        "name": 'rotate left',
        "method": 'rotate',
        "arguments": [-80, 0]
        }, {
        "name": 'rotate up',
        "method": 'rotate',
        "arguments": [0, -40]
        }, {
        "name": 'rotate down',
        "method": 'rotate',
        "arguments": [0, 40]
        }, {
        "name": 'rotate right-up',
        "method": 'rotate',
        "arguments": [80, -40]
        }, {
        "name": 'rotate right-down',
        "method": 'rotate',
        "arguments": [80, 40]
        }, {
        "name": 'rotate left-up',
        "method": 'rotate',
        "arguments": [-80, -40]
        }, {
        "name": 'rotate left-down',
        "method": 'rotate',
        "arguments": [-80, -40]
        }
      ],
      [
        {
        "name": 'drop',
        "method": 'key_press',
        "arguments": [self.drop],
        },
        {
        "name": 'inventory',
        "method": 'toggle_inventory',
        "arguments": [self.inventory],
        }, {
        "name": 'wield hotbar1',
        "method": 'key_press',
        "arguments": [self.slot1],
        }, {
        "name": 'wield hotbar2',
        "method": 'key_press',
        "arguments": [self.slot2],
        }, {
        "name": 'wield hotbar3',
        "method": 'key_press',
        "arguments": [self.slot3],
        }, {
        "name": 'wield hotbar4',
        "method": 'key_press',
        "arguments": [self.slot4],
        }, {
        "name": 'wield hotbar5',
        "method": 'key_press',
        "arguments": [self.slot5],
        }, {
        "name": 'wield hotbar6',
        "method": 'key_press',
        "arguments": [self.slot6],
        }, {
        "name": 'wield hotbar7',
        "method": 'key_press',
        "arguments": [self.slot7],
        }, {
        "name": 'wield hotbar8',
        "method": 'key_press',
        "arguments": [self.slot8],
        }, {
        "name": 'wield hotbar9',
        "method": 'key_press',
        "arguments": [self.slot9],
        }
      ]
    ]

    action_spaces = []
    actions = []
    for group in action_list:
      group.append({
        "name": 'NO OP',
        "method": 'no_op',
        "arguments": [1],
      })
      action_spaces.append(len(group))
      actions.append(group)

    return actions, action_spaces