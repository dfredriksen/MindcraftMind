# MindcraftMind

Intended to be an interface between the Minecraft Desktop Java Edition client (1.15.2) for Windows 10 and a reinforcement learning agent. 

The official RL agent for Minecraft is [Project Malmö](https://github.com/microsoft/malmo). At the time of development, Malmö did not support Minecraft clients greater than 1.11, and I wanted to use the bot on my own Minecraft server (which is purely vanilla). As a result, MindcraftMind and the gym_MinecraftLive project were born. 

It's my intent to use this as a stepping stone for other RL projects where there is not an easy access plugin or API to the target environment.

## Installation

You will need a paid Minecraft account to use MindcraftMind to control an Avatar with vanilla Minecraft

## config.py

A config.py should be setup in the root directory of the repo with the following constants set:

    RESIZE_SIZE = <int> #Size to resize screenshots to using pytorch. Will resize smallest dimension and preserve aspect ratio. Currently should be set to 100 
    MINECRAFT_LAUNCHER_PATH = <string> #Path to Minecraft launcher
    DONE_DATASET = <string> # Path to "done" folder for training dataset contained within repo.
    SCREENSHOT_PATH = <string> # Path to minecraft screenshot directory
    ACTION_STATEPATH = <string> # Path to download the DQN parameters into 
    DONE_STATEPATH = <string> # Path of the "done detector" learning parameters. Should be the modelparams folder in this repo.
    LEARNING_HOST = <string> # Hostname of the DQN Cloud webservice
    DEVICE = <string> #GPU or Cuda
    AWS_ACCESS_KEY = <string> #AWS access key for S3 access
    AWS_SECRET_KEY = <string> #AWS access key for S3 access
    S3_BUCKET_NAME = <string> #S3 bucket name to store processed images
    EPS_START = <float> #The percentage of reward at start before decay is applied
    EPS_END = <float> #The minimum amount of reward after decay
    EPS_DECAY = <int> #The total number of steps before max decay is reached
    CLEAN_THREADS = <int> #Number of steps before cleaning threads from the thread list
    RESOLUTION_WIDTH = <int> #Width of screen resolution. Training data is set to train on 800x600
    RESOLUTION_HEIGHT = <int> #Height of screen resolution

## Under Construction

This repo is under construction

    TODO: Separate DirectInput commands from Minecraft specific functionality into distinct libraries
    TODO: Add Unit Tests
    TODO: Ensure code style is more Pythonic
    TODO: Add cross platform portability
    TODO: Consolidate Done Detector with other CNN class into separate libraries
    TODO: Add support for multiple resolutions
    TODO: Add an easy way to quit with a keypress or similar action so that program doesn't hijack input and run amok
    TODO: Publish package to PyPi
