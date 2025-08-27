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

<details>
<summary> 💡Tips for using 1Password</summary>

> If you use 1password for your secrets, you can use the [op.env](config/op.env) file as a template for generating your config file

- [Install op](https://support.1password.com/command-line-getting-started/)
- Run `op signin`
- I have added a convenience script [scripts/create_local_dev_env.sh](scripts/create_local_dev_env.sh) for creating the env file with `op inject`

</details>

#### Manual file creation
- You can copy / edit the [sample.env](docs/sample.env) and place it in `config/.env.dev`

### Start services with Docker
```bash
docker compose -f compose.dev.yml up -d
```

This will start the web server and any required dependencies (e.g., database).

###  Access the app
Once the containers are running, open:

http://localhost:8000


## Current work on Issue #196

### Prep environment
#### Prep local dev (pycharm)
- make sure you're local .venv is set up
- `uv venv .venv` # creates the local environment
- `uv pip install -r config/requirements.txt`
- Delete all previous docker volumes / images / containers
- run `scripts/create_local_dev_env.sh` to create the development env
- make sure you're interpreter is set to the local .venv
- run `scripts/create_local_python.sh` to make sure your local python environment is ready for development
- install psql tools on your Mac:
```bash
brew install libpq
brew link --force libpq
```
- fire up the dev container `docker compose -f compose.dev.yml up -d`

