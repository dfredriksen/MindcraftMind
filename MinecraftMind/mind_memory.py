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
    for memory_thread in self.memory_threads:
      if memory_thread.is_alive() and memory_thread.name != self.name:
        memory_thread.join()

    filepath = os.path.join(SCREENSHOT_PATH, self.filename)
    s3 = boto3.client(
      "s3",
      aws_access_key_id = AWS_ACCESS_KEY,
      aws_secret_access_key = AWS_SECRET_KEY
    )
    bucket_resource = s3
    in_mem_file = io.BytesIO()
    image_array = np.array(self.image)
    self.image.save(in_mem_file, format=self.image.format)
    data = in_mem_file.getvalue()
    bucket_resource.upload_file(
      Bucket = S3_BUCKET_NAME,
      Body = data,
      Key=self.trial + "/" + self.episode + "/" + self.step + '.png'
    )
    os.remove(filepath)

    post_data = {
      "image": image_array.tolist(),
      "reward": self.reward,
      "step": self.step,
      "trial": self.trial,
      "episode": self.episode,
      "action": self.action,
      "last_state": self.state,
      "next_state": self.next_state,
      "inventory": str(self.inventory),
      "version": self.version
    }

    response = requests.post('http://' + LEARNING_HOST + '/optimize', data=post_data)
    if response.status_code != 200:
      print("Failed to POST step to server - step " + self.step)
    