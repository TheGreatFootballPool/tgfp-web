# Great Football Pool

## Production Deployment

- Docker Compose (Use Portainer)
- Here is the [docker compose](docker-compose.yaml)

## Updating Poetry Packages

When updating to newer version of any package (for example `tgfp-nfl` or `tgfp-lib`):

* `poetry cache clear pypi --all`
* `poetry add tgfp-nfl:latest` or `poetry add tgfp-lib:latest`

## Development process

### Prerequisites

* Cloudflare WARP client installed and connected
* `tgfp-web` and `tgfp` repos cloned

### Gather all the variables you'll need

Instructions below are for 'full stack' dev -- for DB only, just execute steps with [DB] in front

1. [DB] Create the dev stack .env file
   - `create_dev_env.sh`
2. [DB] Get the IP address of your dev machine (we'll call it `<dev_ip_address>` below)
   - `ipconfig getifaddr en0`
3. [DB] Get the production mongo DB password from 1Password `<prod_db_pass>`
   - `python prefect_fetch.py mongo-root-password-production`

### Set up the discord redirect URI

1. go to 'prefect cloud' and change the variable `discord_redirect_uri_development` to `http://<dev_ip_address>:6701/callback` (assuming same port)
2. add the redirect URI to the [Discord Developer Portal](https://discord.com/developers/applications) 

### Start and Initialize the database

1. [DB] Use the [dev docker compose](dev-docker-compose.yaml) file for development
2. [DB] Start the mongo-db service from `dev-docker-compose`
3. [DB] Connect to the terminal of the container
4. [DB] Clone the Prod db for development
   1. `mongodump --username tgfp --password <prod_db_pass> --host="goshdarnedserver.lan:27017"`
   2. `rm -rf dump/admin`
   3. `mongorestore --username tgfp --password development dump/ --authenticationDatabase=admin --drop`
5. [DB] Confirm the DB looks good by checking with mongo compass gui

### Start the web server and log in to test

1. Run the `Flask` Configuration (drop down menu PyCharm)
2. Test log in to Discord

# 2024 TODOS
- [ ] Migrate secrets to 1Password

## Current state
* Simple FastAPI Docker container created

## Next step
* publish docker to docker hub on git push

