#!/usr/bin/env bash
cd "$(dirname "$0")" || exit
bash -c "$(wget -qLO - https://github.com/TheGreatFootballPool/tgfp-web/raw/main/scripts/deploy.sh)"