import boto3, os, io
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY
from config import S3_BUCKET_NAME, SCREENSHOT_PATH, LEARNING_HOST
from threading import Thread
import numpy as np
import requests

class Memory(Thread):

  def __init__(self, environment, filename, done, reward, trial, episode, step, state, next_state, action, inventory, version, memory_threads):
    Thread.__init__(self)
    self.image = environment
    self.filename = filename
    self.done = done
    self.trial = trial
    self.episode = episode
    self.step = step
    self.reward = reward
    self.version = version
    self.state = state
    self.next_state = next_state
    self.action = action
    self.inventory = inventory
    self.memory_threads = memory_threads

  def run(self):
    
    filepath = os.path.join(SCREENSHOT_PATH, self.filename)
    s3 = boto3.client(
      "s3",
      aws_access_key_id = AWS_ACCESS_KEY,
      aws_secret_access_key = AWS_SECRET_KEY
    )
    bucket_resource = s3
    in_mem_file = io.BytesIO()
    image_array = np.array(self.image)
    self.image.save(in_mem_file, format='png')
    in_mem_file.seek(0)
    bucket_resource.upload_fileobj(
      Bucket = S3_BUCKET_NAME,
      Fileobj = in_mem_file,
      Key=str(self.trial) + "/" + str(self.episode) + "/" + str(self.step) + '.png'
    )
    os.remove(filepath)

    post_data = {
      "image": image_array.tolist(),
      "reward": self.reward,
      "step": self.step,
      "trial": self.trial,
      "episode": self.episode,
      "action": self.action.tolist(),
      "last_state": self.state.tolist(),
      "inventory": str(self.inventory),
      "version": self.version
    }

    if(self.next_state is None):
      post_data['next_state'] = None
    else:
      post_data["next_state"]  = self.next_state.tolist()

    response = requests.post('http://' + LEARNING_HOST + '/optimize', json=post_data)
    if response.status_code != 200:
      print("Failed to POST step to server - step " + str(self.step))