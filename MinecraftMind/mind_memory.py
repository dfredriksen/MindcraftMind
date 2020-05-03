import boto3, os, io
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET_NAME, SCREENSHOT_PATH
from threading import Thread

class Memory(Thread):

  def __init__(self, environment, filename, done, reward, trial, episode, step, memory_threads):
    Thread.__init__(self)
    self.state = environment
    self.filename = filename
    self.done = done
    self.trial = trial
    self.episode = episode
    self.step = step
    self.reward = reward
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
    self.state.save(in_mem_file, format=self.state.format)
    data = in_mem_file.getvalue()
    bucket_resource.upload_file(
      Bucket = S3_BUCKET_NAME,
      Body = data,
      Key=self.trial + "/" + self.episode + "/" + self.step + '.png'
    )
    os.remove(filepath)

    print("POST to endpoint goes here")