#!/usr/bin/env bash
INSTALL_DIR=/opt/tgfp
cd $INSTALL_DIR || exit

systemctl stop tgfp-web.service
# Install packages
echo "TGFP: Updating installed packages"
apt update && apt upgrade -y
if ! dpkg -s python3.11 python3.11-venv python3-pip python-is-python3 > /dev/null 2>&1
then
  echo "TGFP: Installing Python"
  apt install python3.11 python3.11-venv python3-pip python-is-python3 -y
fi

echo "TGFP: Fetching / installing web site"
# fetch the tgfp code
wget https://github.com/TheGreatFootballPool/tgfp-web/archive/main.zip
unzip main.zip
rm main.zip

# grab the important bits
rm -rf ${INSTALL_DIR}/app
mv tgfp-web-main/app ${INSTALL_DIR}
mv tgfp-web-main/config/requirements.txt ${INSTALL_DIR}
mv tgfp-web-main/scripts/update.sh ${INSTALL_DIR}
mv tgfp-web-main/config/op.env ${INSTALL_DIR}
mv tgfp-web-main/config/version.env ${INSTALL_DIR}
mv tgfp-web-main/config/tgfp-web.service /etc/systemd/system
mv tgfp-web-main/config/tgfp-bot.service /etc/systemd/system
rm -rf tgfp-web-main

# install python virtualenv and requirements
cd ${INSTALL_DIR}/app || exit
python -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r ${INSTALL_DIR}/requirements.txt
rm ${INSTALL_DIR}/requirements.txt

# install op so we can create the .env
if ! dpkg -s 1password-cli > /dev/null 2>&1
then
  echo "TGFP: Installing 1password-cli"
  apt install gpg -y
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
  apt update && apt install 1password-cli -y
  echo "Installed 1password!"
fi

if ! test -e ${INSTALL_DIR}/op-token.env
then
  echo "TGFP: Getting 1password token"
  read -r -p "Enter 1password auth token: " onepassword_auth_token
  export OP_SERVICE_ACCOUNT_TOKEN=${onepassword_auth_token}
  echo "export OP_SERVICE_ACCOUNT_TOKEN=${onepassword_auth_token}" > ${INSTALL_DIR}/op-token.env
else
  source ${INSTALL_DIR}/op-token.env
fi

if ! test -e ${INSTALL_DIR}/environment.env
then
  echo "TGFP: Getting env"
  echo "Choose to run as dev env or prod"
  read -r -p "Default is to run in production, deploy to DEVELOPMENT env[Y/y]: " dev_env
  if [[ $dev_env == "y" || $dev_env == "Y" ]] ; then
    ENV="development"
  else
    ENV="production"
  fi
  echo "export ENV=${ENV}" > ${INSTALL_DIR}/environment.env
else
  source ${INSTALL_DIR}/environment.env
fi

# Create the .env file
APP_ENV=${ENV} op inject -f -i ${INSTALL_DIR}/op.env -o ${INSTALL_DIR}/app/.env
# Add the current run env to the .env file
echo "ENVIRONMENT=${ENV}" >> ${INSTALL_DIR}/app/.env

# Add the current VERSION to the .env file
source ${INSTALL_DIR}/version.env
NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo "APP_VERSION=${NEW_VERSION}" >> ${INSTALL_DIR}/app/.env
rm ${INSTALL_DIR}/op.env

systemctl daemon-reload
systemctl enable tgfp-web.service
systemctl start tgfp-web.service
systemctl enable tgfp-bot.service
systemctl start tgfp-bot.service

