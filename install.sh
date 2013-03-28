#!/bin/bash

#Gets the directory the files are in ( should be the same directory this script is in )
echo Determining the base directory
basedir=$(pwd)/$(dirname $0)
echo $basedir
#Creates necessary directories and files in the home directory
echo Creating necessary directories and files in the home directory
mkdir -p ~/.amazonCheck
mkdir -p ~/.amazonCheck/pics
cp -v $basedir/icons/empty_image.png ~/.amazonCheck/pics/
touch ~/.amazonCheck/aC.log
touch ~/.amazonCheck/aC.data
touch ~/.amazonCheck/aC.config

#Copies the application to its specific destination
echo Copying the application to it\'s specific destination
sudo cp -v $basedir/amazonCheck.py /usr/bin/amazonCheck

#Copies the .desktop file to its specific destination
echo Copying the .desktop file to it\'s specific destination
sudo cp -v $basedir/amazonCheck.desktop /usr/share/applications/


#Copies the icon files to their specific destinations
echo Copying the icon files to their specific destinations
sudo cp -v $basedir/icons/icon.png /usr/share/pixmaps/amazonCheck.png
sudo cp -v $basedir/icons/indicator.png /usr/share/pixmaps/amazonCheck_indicator.png
sudo cp -v $basedir/icons/indicator_attention.png /usr/share/pixmaps/amazonCheck_indicator_attention.png

#Installs necessary libraries ( python2.7 should be installed )
echo Installing the necessary libraries \( python2.7 should be installed \)
echo /usr/lib/python* | xargs -n 1 sudo cp -v $basedir/lib/amazonCheckLib.py
echo /usr/lib/python* | xargs -n 1 sudo cp -v $basedir/lib/amazonCheckTrans.py
echo /usr/lib/python* | xargs -n 1 sudo cp -v $basedir/lib/colors.py
