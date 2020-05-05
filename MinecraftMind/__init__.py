def main():
  from mind import Mind
  minecraft_mind = Mind()
  minecraft_mind.learning_loop()

def train_cnn_done():
  from mind_cnn_done import detect_is_done, CNNDone, train_done_detector
  import numpy as np
  from PIL import Image
  from config import DONE_STATEPATH
  import torch
  done_model = CNNDone()
  train_done_detector(done_model, 100)
  #done_model.load_state_dict(torch.load(DONE_STATEPATH))
  #im = Image.open("C:\\Users\\dfred\\Downloads\\2.png")
  #r_im = done_model.process_image(im)
  #c_im = done_model.crop_image(r_im)
  #print(str(detect_is_done(c_im, done_model)))
  #main()

if __name__ == "__main__":
  #train_cnn_done()
  main()