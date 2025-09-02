# Great Football Pool

# Installation notes

The great football pool is self-contained in a docker environment.

## Development Process

Follow these steps to get the project running locally for development.

### Prerequisites
* Docker (compose)

### 1. Clone the repository
```bash
git clone git@github.com:TheGreatFootballPool/tgfp-web.git
cd tgfp-web
```

### Steps for deployment
### 2. Create the CONFIG file: 
> This file is needed by [compose.prod.yml](compose.prod.yml)

* _Production_: `config/.env.production`
* _Development_: `config/.env.development`

> See the `config/sample.env` for example config
 
<details>

<summary> 💡How to use 1Password to generate .env file </summary>

> If you use 1password for your secrets, you can use the [op.env](config/op.env) file as a template for generating your config file

- [Install op](https://support.1password.com/command-line-getting-started/)
- `export OP_SERVICE_ACCOUNT_TOKEN=<your token>`
- `op vault list` (to test)
- Run the convenience script to create the env file with `op inject`
  - Production [scripts/create_local_prod_env.sh](scripts/create_local_prod_env.sh) 
  - Development [scripts/create_local_dev_env.sh](scripts/create_local_dev_env.sh)
</details>

### Start services with Docker
```bash
docker compose -f compose.dev.yml up -d
```

This will start the web server and any required dependencies (e.g., database).

###  Access the app
Once the containers are running, open:

(example for local) http://localhost:6701/


### Prep environment
#### Prep local dev (pycharm - not container)

NOTE: Do the following BEFORE starting pycharm
- checkout the code
- cd into dir
- run `scripts/create_local_python.sh` to make sure your local python environment is ready for development
- fire up pycharm
- make sure you're interpreter is set to the local .venv
- Delete all previous docker volumes / images / containers
- install (or confirm) psql tools on your Mac:
```bash
brew install libpq
brew link --force libpq
```
- run `scripts/create_local_dev_env.sh` to create the development env
- fire up the dev container for DB `docker compose -f compose.dev.yml up -d --build postgres`
- fire up the tgfp-web site locally
NOTE: Don't worry about the web site not firing up yet, we'll get to that

### Initialize the Postgresql DB
- read in the config
```bash
set -a
source config/.env.development
set +a
```

