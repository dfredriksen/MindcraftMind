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

  def __init__(self):
    return None

  def enumerate_actions(self, mind):
    return [{
      "name": 'move forward',
      "method": mind.key_press,
      "arguments": [self.forward]
    },{ 
      "name": 'strafe left',
      "method": mind.key_press,
      "arguments": [self.left]
    },{
      "name": 'strafe right',
      "method": mind.key_press,
      "arguments": [self.right]
    },{
      "name": 'backpedal',
      "method": mind.key_press,
      "arguments": [self.back]
    }, {
      "name": 'drop item',
      "method": mind.key_press,
      "arguments": [self.drop]
    }, {
      "name": 'jump',
      "method": mind.key_press,
      "arguments": [self.jump]
    }, {
      "name": 'inventory',
      "method": mind.key_press,
      "arguments": [self.inventory]
    }, {
      "name": 'wield hotbar1',
      "method": mind.key_press,
      "arguments": [self.slot1]
    }, {
      "name": 'wield hotbar2',
      "method": mind.key_press,
      "arguments": [self.slot2]
    }, {
      "name": 'wield hotbar3',
      "method": mind.key_press,
      "arguments": [self.slot3]
    }, {
      "name": 'wield hotbar4',
      "method": mind.key_press,
      "arguments": [self.slot4]
    }, {
      "name": 'wield hotbar5',
      "method": mind.key_press,
      "arguments": [self.slot5]
    }, {
      "name": 'wield hotbar6',
      "method": mind.key_press,
      "arguments": [self.slot6]
    }, {
      "name": 'wield hotbar7',
      "method": mind.key_press,
      "arguments": [self.slot7]
    }, {
      "name": 'wield hotbar8',
      "method": mind.key_press,
      "arguments": [self.slot8]
    }, {
      "name": 'wield hotbar9',
      "method": mind.key_press,
      "arguments": [self.slot9]
    }, {
      "name": 'left click',
      "method": mind.mouse_click,
      "arguments": [0, 0, 'left']
    }, {
      "name": 'right click',
      "method": mind.mouse_click,
      "arguments": [0, 0, 'right']
    }, {
      "name": 'left mouse press',
      "method": mind.mouse_down,
      "arguments": [0, 0, 'left']
    }, {
      "name": 'right mouse press',
      "method": mind.mouse_down,
      "arguments": [0, 0, 'right']
    }, {
      "name": 'left mouse release',
      "method": mind.mouse_up,
      "arguments": [0, 0, 'left']
    }, {
      "name": 'right mouse release',
      "method": mind.mouse_up,
      "arguments": [0, 0, 'right']
    }, {
      "name": 'rotate',
      "method": mind.mouse_move,
      "arguments": [0, 0]
    }]