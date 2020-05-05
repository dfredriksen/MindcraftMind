import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from torch.optim import Adam, SGD
import os
from PIL import Image
import torchvision.transforms as T
from config import RESIZE_SIZE, DONE_DATASET, DONE_STATEPATH, DEVICE, RESOLUTION_HEIGHT, RESOLUTION_WIDTH
import numpy as np
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score
import time

class CNNDone(nn.Module):
  
  resize = T.Compose([T.Resize(RESIZE_SIZE, interpolation=Image.CUBIC)])
  TRAINING_DATASET = os.path.join(DONE_DATASET, "train")
  TEST_DATASET = os.path.join(DONE_DATASET, "test")
  train_x = None
  train_y = None
  test_x = None
  test_y = None
  to_tensor = T.Compose([T.ToTensor()])

  def __init__(self):
      super(CNNDone, self).__init__()
      linear_input_size = 4 * 20 * 6
      self.cnn_layers = nn.Sequential(
        # Defining a 2D convolution layer
        nn.Conv2d(1, 4, kernel_size=3, stride=1, padding=1),
        nn.BatchNorm2d(4),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(kernel_size=2, stride=2),
        # Defining another 2D convolution layer
        nn.Conv2d(4, 4, kernel_size=3, stride=1, padding=1),
        nn.BatchNorm2d(4),
        nn.ReLU(inplace=True),
        nn.MaxPool2d(kernel_size=2, stride=2),
      )

      self.linear_layers = nn.Sequential(
          nn.Linear(linear_input_size, 2)
      )

  # Called with either one element to determine next action, or a batch
  # during optimization. Returns tensor([[left0exp,right0exp]...]).
  def forward(self, x):
    x = self.cnn_layers(x)
    x = x.view(x.size(0), -1)
    x = self.linear_layers(x)
    return x

  def conv2d_size_out(self, size, kernel_size = 3, stride = 1):
          return (size - (kernel_size - 1) - 1) // stride  + 1

  def load_training_data(self):
    TRAINING_DEAD_PATH = os.path.join(self.TRAINING_DATASET, 'dead')
    TRAINING_NOT_DEAD_PATH = os.path.join(self.TRAINING_DATASET, 'not_dead')
    TEST_DEAD_PATH = os.path.join(self.TEST_DATASET, 'dead')
    TEST_NOT_DEAD_PATH = os.path.join(self.TEST_DATASET, 'not_dead')
    train_dead_images = os.listdir(TRAINING_DEAD_PATH)
    train_not_dead_images = os.listdir(TRAINING_NOT_DEAD_PATH)
    test_dead_images = os.listdir(TEST_DEAD_PATH)
    test_not_dead_images = os.listdir(TEST_NOT_DEAD_PATH)
    
    train_data = {
      "image": [],
      "label": []
    }

    test_data = {
      "image": [],
      "label": []
    }

    for dead_image in train_dead_images:
      s_im = self.process_image_test(os.path.join(TRAINING_DEAD_PATH,dead_image))
      train_data["image"].append(s_im)
      train_data["label"].append(1)
    
    for not_dead_image in train_not_dead_images:
      s_im = self.process_image_test(os.path.join(TRAINING_NOT_DEAD_PATH,not_dead_image))
      train_data["image"].append(s_im)
      train_data["label"].append(0)

    for dead_image in test_dead_images:
      s_im = self.process_image_test(os.path.join(TEST_DEAD_PATH,dead_image))
      test_data["image"].append(s_im)
      test_data["label"].append(1)
    
    for not_dead_image in test_not_dead_images:
      s_im = self.process_image_test(os.path.join(TEST_NOT_DEAD_PATH,not_dead_image))
      test_data["image"].append(s_im)
      test_data["label"].append(0)
    
    self.train_x = train_data["image"]
    self.train_y = np.array(train_data["label"]).astype(float)
    self.test_x = test_data["image"]
    self.test_y = np.array(test_data["label"]).astype(float)  
    self.train_x, self.val_x, self.train_y, self.val_y = train_test_split(self.train_x, self.train_y, test_size = 0.1)
  
  def process_image_test(self, img_path):
    im = Image.open(img_path)
    r_im = self.process_image(im)
    a_im = self.crop_image(r_im)
    return a_im

  def crop_image(self, r_im):
    w,h = (RESOLUTION_WIDTH, RESOLUTION_HEIGHT)
    rw,rh = r_im.size
    wf = rw/w
    hf = rh/h
    c_im = T.functional.crop(r_im, int(115*hf), int(305*wf), int(160*hf), int(495*wf))
    b_im = c_im.convert("1", dither=Image.NONE)
    a_im = np.array(b_im).astype(float)
    return a_im

  def process_image(self, im):
    return self.resize(im)

def train_model(epochs, model):
    train_losses = []
    val_losses = []
    for epoch in range(epochs):
      optimizer = Adam(model.parameters(), lr=0.07)
      criterion = nn.CrossEntropyLoss()
      model.train()
      tr_loss = 0
      x_train = Variable(torch.tensor(model.train_x).unsqueeze(1)).float()
      y_train = Variable(torch.tensor(model.train_y).unsqueeze(1)).float()
      x_val = Variable(torch.tensor(model.val_x).unsqueeze(1)).float()
      y_val = Variable(torch.tensor(model.val_y).unsqueeze(1)).float()
      optimizer.zero_grad()
      output_train = model(x_train)
      output_val = model(x_val)
      loss_train = criterion(output_train, y_train.squeeze().long())
      loss_val = criterion(output_val, y_val.squeeze().long())
      train_losses.append(loss_train)
      val_losses.append(loss_val)
      loss_train.backward()
      optimizer.step()
      tr_loss = loss_train.item()
      if epoch%2 == 0:
        print('Epoch : ',epoch+1, '\t', 'loss :', loss_val)
      # plotting the training and validation loss
    start_time = time.time()
    print('Predicting training set')
    predict_set(x_train, y_train, model)
    end_time = time.time()
    print('Prediction of ' + str(len(x_train)) + ' samples took ' + str(end_time - start_time) + ' seconds')
    print('Predicting validation set')
    predict_set(x_val, y_val, model) 
    test_x = Variable(torch.tensor(model.test_x).unsqueeze(1)).float()
    test_y = Variable(torch.tensor(model.test_y).unsqueeze(1)).float()
    print('Predicting test set')
    predict_set(test_x, test_y, model)
    torch.save(model.state_dict(), DONE_STATEPATH)
    plt.plot(train_losses, label='Training loss')
    plt.plot(val_losses, label='Validation loss')
    plt.legend()
    plt.show()


def predict_set(set_values, labels, model):
    predictions = is_done(set_values, model)
    print(str(accuracy_score(labels, predictions)*100) + '% accuracy on target dataset')

def detect_is_done(np_value, model):
    value = Variable(torch.tensor([np_value]).unsqueeze(1)).float()
    return bool(is_done(value, model)[0])

def is_done(value, model):
    with torch.no_grad():
        output = model(value)

    softmax = torch.exp(output)
    prob = list(softmax.numpy())
    return np.argmax(prob, axis=1)

def train_done_detector(model = None, epochs=25, w = 800, h = 600):
  if model == None:
    model = CNNDone()
  model.load_training_data()
  train_model(epochs, model)
