#!/bin/bash

#Gets the directory the files are in ( should be the same directory this script is in )
echo Determining the base directory
basedir=$(pwd)/$(dirname $0)
echo $basedir
#Creates necessary directories and files in the home directory
echo Creating necessary directories and files in the home directory
mkdir -p ~/.amazonCheck
mkdir -p ~/.amazonCheck/pics
mkdir -p ~/.amazonCheck/pics/icons
touch ~/.amazonCheck/log
touch ~/.amazonCheck/data
touch ~/.amazonCheck/config

#Copies the application to its specific destination
echo Copying the application to it\'s specific destination
sudo cp -v $basedir/amazonCheck.py /usr/bin/amazonCheck

#Copies the .desktop file to its specific destination
echo Copying the .desktop file to it\'s specific destination
sudo cp -v $basedir/amazonCheck.desktop /usr/share/applications/

#Installs necessary libs
echo Installs necessary libs
cd $basedir/lib
sudo python setup.py install
cd -

#Copies the icon files to their specific destinations
echo Copying the icon files to their specific destinations
cp -v $basedir/icons/icon-100px.png ~/.amazonCheck/pics/icons/icon.png
cp -v $basedir/icons/indicator.png ~/.amazonCheck/pics/icons/ind_act.png
cp -v $basedir/icons/indicator_attention.png ~/.amazonCheck/pics/icons/ind_att.png
