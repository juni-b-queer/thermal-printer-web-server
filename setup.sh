#!/usr/bin/bash

sudo apt-get install python-dev

sudo pip3 install -r requirements.txt --break-system-packages
sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel --break-system-packages
sudo python3 -m pip install --force-reinstall adafruit-blinka

