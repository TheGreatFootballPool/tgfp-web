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
mv tgfp-web-main/app ${INSTALL_DIR}
mv tgfp-web-main/requirements.txt ${INSTALL_DIR}
mv tgfp-web-main/op.env ${INSTALL_DIR}
rm -rf tgfp-web-main

# install python virtualenv and requirements
cd ${INSTALL_DIR}/app || exit
python -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r ${INSTALL_DIR}/requirements.txt

# install op so we can create the .env
apt install gpg
curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" |
tee /etc/apt/sources.list.d/1password.list
mkdir -p /etc/debsig/policies/AC2D62742012EA22/
curl -sS https://downloads.1password.com/linux/debian/debsig/1password.pol | \
tee /etc/debsig/policies/AC2D62742012EA22/1password.pol
mkdir -p /usr/share/debsig/keyrings/AC2D62742012EA22
curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
gpg --dearmor --output /usr/share/debsig/keyrings/AC2D62742012EA22/debsig.gpg
apt update && apt install 1password-cli

echo "Installed 1password!"
read -r -p "Enter 1password auth token: " onepassword_auth_token
export OP_SERVICE_ACCOUNT_TOKEN=${onepassword_auth_token}

echo "Choose to run as dev env or prod"
read -r -p "Default is to run in production, deploy to DEVELOPMENT env[Y/y]: " dev_env
if [[ $dev_env == "y" || $dev_env == "Y" ]] ; then
  ENV="development"
else
  ENV="production"
fi
echo "ENV set to ${ENV}"

APP_ENV=${ENV} op inject -f -i ${INSTALL_DIR}/op.env -o ${INSTALL_DIR}/app/.env
echo "ENVIRONMENT=${ENV}" >> ${INSTALL_DIR}/app/.env

# fire up the app
# uvicorn --host 0.0.0.0 --port 6701 main:app

