#!/bin/sh
x-terminal-emulator -e "cd ./democz; ../../venvDemocz/bin/python 'democzOOP.py'; bash"
sleep 8s
x-terminal-emulator -e "cd ./gui;   ../../venvDemocz/bin/python 'guiOOP.py'; bash"
