from setuptools import setup, find_packages

setup(name='MinecraftMind',
  version='0.0.1',
  install_requires=['pywin32', 'pyautogui', 'subprocess_maximize', 'opencv-python','pytesseract', 'cv'],
  description='A tool for controlling Vanilla Mindcraft without requiring mods or plugins',
  author = 'Daniel Fredriksen',
  author_email = 'dfredriksen@cyint.technology',
  url='https://github.com/dfredriksen/MindcraftMind',
  packages=find_packages(where='MinecraftMind'),
  include_package_data=True
)
