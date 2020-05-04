from threading import Thread, Event
import requests
from mind_dqn import DQN
from config import DEVICE, LEARNING_HOST, ACTION_STATEPATH
import torch

class PolicyLoader(Thread):

    def __init__(self, width, height, outputs):
        Thread.__init__(self)
        self.new_net = DQN(width, height, outputs).to(DEVICE)
        self.new_version = None
        self.loaded = False
        self._stopevent = Event()

    def run(self):
        self.new_version = get_policy_version()
        if(self.new_version == 1):
            self._stopevent.set()
        else:
            download_policy(self.new_version)
            self.new_net.load_state_dict(torch.load(ACTION_STATEPATH))
            self.new_net.eval()
        self.loaded = True

def get_policy_version():
    response = requests.get('http://' + LEARNING_HOST + "/version")
    if response.status_code != 200:
      print("Could not obtain policy version from the learning module!")
      return 1
    else:
      return response.text

def download_policy(version):
    response = requests.get('http://' + LEARNING_HOST + "/policy?version=" + version)
    f = open(ACTION_STATEPATH, 'w+b')
    f.write(response.content)
    f.close()