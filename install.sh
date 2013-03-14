#!/bin/bash

#Gets the directory the files are in ( should be the same directory this script is in )
basedir=$(pwd)/$(dirname $0)

#Creates necessary directories and files in the home directory
mkdir -p ~/.amazonCheck
mkdir -p ~/.amazonCheck/pics
touch ~/.amazonCheck/aC.log
touch ~/.amazonCheck/aC.data
touch ~/.amazonCheck/aC.config

#Copies the application to its specific destination
sudo cp -v $basedir/amazonCheck.py /usr/bin/amazonCheck

#Copies the .desktop file to its specific destination
sudo cp -v $basedir/amazonCheck.desktop /usr/share/applications/

#Copies the icon file to its specific destinations
sudo cp -v $basedir/icons/icon.png /usr/share/pixmaps/amazonCheck.png
sudo cp -v $basedir/icons/indicator.png /usr/share/pixmaps/amazonCheck_indicator.png
sudo cp -v $basedir/icons/indicator_attention.png /usr/share/pixmaps/amazonCheck_indicator_attention.png

#Installs necessary libraries ( python should be installed )
echo /usr/lib/python* | xargs -n 1 sudo cp -v $basedir/lib/amazonCheckLib.py
echo /usr/lib/python* | xargs -n 1 sudo cp -v $basedir/lib/amazonCheckTrans.py
echo /usr/lib/python* | xargs -n 1 sudo cp -v $basedir/lib/colors.py
