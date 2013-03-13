#!/bin/bash

#Gets the directory the files are in ( should be the same directory this script is in )
basedir=$(pwd)/$(dirname $0)

#Creates necessary directories and files in the home directory
mkdir -p ~/.amazonCheck
mkdir -p ~/.amazonCheck/pics
touch ~/.amazonCheck/aC.log
touch ~/.amazonCheck/aC.data
touch ~/.amazonCheck/aC.config
cp -v $basedir/icon.png ~/.amazonCheck/aC.png

#Copies the application to its specific destination
sudo cp -v $basedir/amazonCheck.py /usr/bin/amazonCheck

#Copies the .desktop file to its specific destination
sudo cp -v $basedir/amazonCheck.desktop /usr/share/applications/

#Copies the icon file to its specific destinations
sudo cp -v $basedir/icon.png /usr/share/pixmaps/amazonCheck.png

#Installs necessary libraries ( python should be installed )
echo /usr/lib/python* | xargs -n 1 sudo cp -v $basedir/amazonCheckLib.py
echo /usr/lib/python* | xargs -n 1 sudo cp -v $basedir/amazonCheckTrans.py
echo /usr/lib/python* | xargs -n 1 sudo cp -v $basedir/colors.py
