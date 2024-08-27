#!/usr/bin/env bash
INSTALL_DIR=/opt/tgfp
cd $INSTALL_DIR || exit

# Install packages
apt update && apt upgrade -y
apt -y install python3.11 python3.11-venv
apt install python3-pip -y
apt install python-is-python3

# fetch the tgfp code
wget https://github.com/TheGreatFootballPool/tgfp-web/archive/main.zip
unzip main.zip
# grab the important bits
mv tgfp-web-main/app $INSTALL_DIR
mv tgfp-web-main/requirements.txt $INSTALL_DIR
rm -rf tgfp-web-main

# install python virtualenv and requirements
cd $INSTALL_DIR/app || exit
python -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r $INSTALL_DIR/requirements.txt

# fire up the app
uvicorn --host 0.0.0.0 --port 6701 main:app

