# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Great Football Pool (TGFP) is a FastAPI-based web application for running an NFL pick'em pool. Users authenticate via Discord, make weekly picks on NFL games, and track standings/awards throughout the season.

## Development Environment Setup

### Initial Setup (PyCharm - Local Development)

1. **Setup local Python environment:**
   ```bash
   scripts/create_local_python.sh
   ```
   This creates a `.venv` with all dependencies from `config/requirements.txt` using `uv pip`.

2. **Create environment configuration:**
   ```bash
   scripts/create_local_dev_env.sh
   ```
   This generates `config/.env.development` from 1Password using the `config/op.env` template.
   Alternatively, manually create config files based on `config/op.env` structure.

3. **Start PostgreSQL database:**
   ```bash
   docker compose -f compose.dev.yml up -d postgres
   ```
   PostgreSQL runs on port 5433 (container port 5432).

4. **Load environment variables:**
   ```bash
   set -a
   source config/.env.development
   set +a
   ```

5. **Run database migrations:**
   ```bash
   scripts/alembic_upgrade_head.sh
   ```

6. **Setup git hooks (recommended):**
   ```bash
   scripts/setup_git_hooks.sh
   ```
   This configures a pre-push hook that ensures `config/version.env` is updated before pushing code changes.

7. **Start the application locally:**
   Run `app/main.py` directly (configured for port 6801 with hot reload when `ENVIRONMENT=local_dev`).

### Docker Development

```bash
# Start all services (web + postgres)
docker compose -f compose.dev.yml up -d --build

# Access at http://localhost:6701/
```

## Common Commands

### Testing and Linting

```bash
# Run all tests and linters
scripts/test_and_lint.sh

# Individual commands:
pytest                                          # Run tests
pylint $(git ls-files '*.py')                  # Lint Python files
flake8 $(git ls-files '*.py') --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics
```

### Database Migrations (Alembic)

```bash
# Generate new migration (auto-detects schema changes)
scripts/alembic_generate_migration.sh "migration message"

# Apply migrations
scripts/alembic_upgrade_head.sh

# Note: These scripts automatically load config/.env.local_dev
```

### Deployment

```bash
# Production deployment
scripts/deploy.sh
```

**Note:** Update `config/version.env` manually before pushing code changes (enforced by pre-push hook).

### Git Hooks

```bash
# Setup git hooks (ensures version.env is updated before push)
scripts/setup_git_hooks.sh

# Bypass hooks for a single push (not recommended)
git push --no-verify
```

**Note:** The pre-push hook prevents pushing code changes without updating `config/version.env`. This ensures all deployments have proper version tracking.

## Architecture

### Core Components

**FastAPI Application (`app/main.py`):**
- Main entry point with lifespan management
- Configures APScheduler for automated jobs
- Includes routers: auth (Discord OAuth), mail, admin
- Session-based authentication via Discord cookies
- Sentry integration for error tracking

**Database Layer (`app/db/__init__.py`):**
- SQLAlchemy with SQLModel ORM
- Primary engine: main PostgreSQL database
- Scheduler engine: separate DB for APScheduler job persistence (defaults to main DB unless `SCHED_DB_URL` set)
- `session_scope()` context manager for transactions

**Models (`app/models/`):**
Core domain models:
- `Player`: Discord-authenticated users
- `Game`: NFL games with ESPN data
- `Team`: NFL teams with records/standings
- `PlayerGamePick`: Individual weekly picks (lock, upset flags)
- `Award`: Achievement types (e.g., "Perfect Week")
- `PlayerAward`: Award instances earned by players
- `ApiKey`: API authentication tokens

**Job Scheduler (`app/jobs/scheduler.py`):**
APScheduler with SQLAlchemyJobStore manages recurring tasks:
- `schedule_nag_players()`: Reminds players to submit picks (60/20/7 min before kickoff)
- `schedule_update_games()`: Polls ESPN API every 5 min during games to update scores
- `schedule_create_picks()`: Creates weekly pick pages (Wed 6am PT)
- `schedule_sync_team_records()`: Updates team standings (Tue 4am PT)
- `schedule_award_updates()`: Recalculates player awards (Tue 5:30am PT)

**NFL Data Integration (`app/tgfp_nfl/tgfp_nfl.py`):**
- Wrapper around ESPN API (`site.api.espn.com`)
- Fetches games, teams, standings, odds/spreads
- HTTP retry logic with exponential backoff for transient errors
- Season types: 1=Preseason, 2=Regular, 3=Postseason

**Routers:**
- `auth.py`: Discord OAuth flow (login, callback)
- `admin.py`: Admin-only endpoints
- `mail.py`: Email notifications (pick reminders, standings)

**Templates (`app/templates/`):**
Jinja2 templates (`.j2` files) for HTML pages: picks, standings, home, etc.

### Key Workflows

**Player Submits Picks:**
1. User navigates to `/picks` (requires Discord auth cookie)
2. Form displays valid games (only pre-kickoff games shown)
3. POST to `/picks_form` validates:
   - All games have picks
   - Lock selection matches an actual pick
   - Upset selection matches an actual pick
4. Creates `PlayerGamePick` records with flags (`is_lock`, `is_upset`)
5. Triggers award recalculation job

**Game Score Updates:**
1. Scheduler starts polling ESPN API 5 minutes before kickoff
2. Updates continue every 5 min (with 60s jitter) for 8 hours
3. Game status tracked: `STATUS_SCHEDULED`, `STATUS_FINAL`, etc.
4. Awards recalculated when games finish

**Award Calculation (`app/jobs/award_update_all.py`):**
- Runs on startup, after picks submission, and weekly on Tuesday
- Each `Award` type has helper logic in `app/models/award_helpers.py`
- Creates/updates `PlayerAward` records

## Configuration

All configuration via environment variables (see `config/op.env` for template):
- `DATABASE_URL`: PostgreSQL connection string
- `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI`: OAuth settings
- `SENTRY_DSN`: Sentry error tracking
- `ENVIRONMENT`: `local_dev`, `development`, or `production`
- `SESSION_SECRET_KEY`: FastAPI session encryption
- `APP_VERSION`: Deployed version (from `config/version.env`)

## Important Notes

- **Authentication:** Discord OAuth only. Cookie `tgfp-discord-id` stores authenticated user.
- **Timezones:** Jobs scheduled in Pacific time (`America/Los_Angeles`), but stored as UTC.
- **Pick Locking:** Once first game of the week starts, picks for games that have started are locked (enforced in `/picks` route).
- **ESPN API:** External dependency; retry logic handles transient failures. Package `tgfp-nfl==6.3.3` wraps API.
- **Alembic Migrations:** Auto-generated; `scripts/alembic_generate_migration.sh` uses probe file to detect actual schema changes.
- **Local Development:** PyCharm setup runs app outside Docker for faster iteration (port 6801); database runs in Docker (port 5433).
