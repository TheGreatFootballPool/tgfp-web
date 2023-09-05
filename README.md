# Great Football Pool

## Production Deployment

- Docker Compose (Use Portainer)
- Here is the [docker compose](docker-compose.yaml)

## Updating Poetry Packages

When updating to newer version of any package (for example `tgfp-nfl` or `tgfp-lib`):

* `poetry cache clear pypi --all`
* `poetry add tgfp-nfl:latest` or `poetry add tgfp-lib:latest`

## Development process

### Gather all the variables you'll need

1. Get the IP address of your dev machine (we'll call it `<dev_ip_address>` below)
   - `ipconfig getifaddr en0`
2. Get the `DISCORD_CLIENT_SECRET` from 1Password
   - `op read op://tgfp/DISCORD/production/client_secret`
3. Generate a UUID for the `SECRET_KEY`
   - `curl https://www.uuidgenerator.net/api/guid`
4. Get the production mongo DB password from 1Password `<prod_db_pass>`
   - `op read op://tgfp/MONGO/production/initdb_root_password`
5. Get the production mongo IP address `<prod_ip_address>`
   - `nslookup goshdarnedserver.lan`

### Create the .env file

1. copy the [dev.env](dev.env) file to `.env`
2. change the `DISCORD_REDIRECT_URI` to `http://<dev_ip_address>:6701/callback` (assuming same port)
3. add the redirect URI to the [Discord Developer Portal](https://discord.com/developers/applications) 
4. change the `DISCORD_CLIENT_SECRET` to the `<discord_client_secret>` from step 2 above
5. change the `SECRET_KEY` to the UUID generated in step 3 above
6. [optional] change the mongo password to whatever you want (update the MONGO_URI)

### Initialize the database

1. Use the [dev docker compose](dev-docker-compose.yaml) file for development
2. Start the mongo-db service from `dev-docker-compose`
3. Connect to the terminal of the container
4. Clone the Prod db for development
   1. `mongodump --username tgfp --password <prod_db_pass> --host="<prod_ip_address>:27017"`
   2. `rm -rf dump/admin`
   3. `mongorestore --username tgfp --password development dump/ --authenticationDatabase=admin --drop`

### Start the web server and log in to test

1. Run the `Flask` Configuration (drop down menu PyCharm)
2. Test log in to Discord