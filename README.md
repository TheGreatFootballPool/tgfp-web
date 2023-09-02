# Great Football Pool

### Production Deployment

- Docker Compose (Use Portainer)
- Here is the [docker compose](docker-compose.yaml)

### Updating Poetry Packages

When updating to newer version of any package (for example `tgfp-nfl` or `tgfp-lib`):
* `poetry cache clear pypi --all`
* `poetry add tgfp-nfl:latest` or `poetry add tgfp-lib:latest`

## Development process
1. Get the IP address of your dev machine (we'll call it `<dev_ip_address>` below)
2. Prepare the docker compose (for running the mongodb and test deployment of web)
   - Use the <dev docker compose](dev-docker-compose.yaml) file for development
   - create a .env file (see the portainer stack)
   - change `OAUTHLIB_INSECURE_TRANSPORT` to `true`
   - change the `DISCORD_REDIRECT_URI` to `http://<dev_ip_address>:6701/callback` (assuming same port)
   - change the mongo password to whatever you want (update the MONGO_URI)
   - change the `SECRET_KEY`
3. Start the mongo-db service from `dev-docker-compose`
4. Connect to the terminal of the container
5. Clone the Prod db for development
   1. `mongodump --username tgfp --password <password> --host="<dev_ip_address>:27017"`
   2. `rm -rf dump/admin`
   3. `mongorestore --username tgfp --password development dump/ --authenticationDatabase=admin`

That's it, you should be able to run the 'Flask' PyCharm Run config now
