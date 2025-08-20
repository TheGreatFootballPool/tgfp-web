# Great Football Pool

# Installation notes

The great football pool is self-contained in a docker environment.

## Development Process

Follow these steps to get the project running locally for development.

### Prerequisites

### Clone the repository
```bash
git clone git@github.com:TheGreatFootballPool/tgfp-web.git
cd tgfp-web
```
### Create the CONFIG file: `config/.env.dev file`
- This file is needed by [compose.dev.yml](compose.dev.yml)

#### 1Password
- If you use 1password for your secrets you can use the [op.env](config/op.env) file as a template for generating your config file
- I have added a convenience script [create_local_dev_env.sh](scripts/create_local_dev_env.sh) for creating the env file with `op inject`

#### Manual file creation
- Otherwise, you can copy / edit the [sample.env](docs/sample.env) and place it in `config/.env.dev`


### Start services with Docker
```bash
docker compose -f compose.dev.yml up -d
```

This will start the web server and any required dependencies (e.g., database).

### Sync production database (optional)
If you need a local copy of the production database for testing:

```bash
scripts/sync_dev_db.sh
```
(see script here) [scripts/sync_dev_db.sh](scripts/sync_dev_db.sh)

> ⚠️ **Note:** Be careful with production data. Ensure credentials and dumps are handled securely.

###  Access the app
Once the containers are running, open:

http://localhost:8000
