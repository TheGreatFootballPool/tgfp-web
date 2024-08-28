# Great Football Pool

# Installation notes

I am going to install this on a Debian 12 LXC hosted by a proxmox instance.  I'm dedicating the LXC for this, so these instructions assume a dedicated container / machine.

## First Time Deployment

On a fresh debian 12 install

```bash
# Run as root
mkdir /opt/tgfp
cd /opt/tgfp
bash -c "$(wget -qLO - https://github.com/tteck/Proxmox/raw/main/ct/mongodb.sh)"
```

## Script steps
apt update && apt upgrade -y