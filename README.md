# Reduction Railroad

## Layout

- `web/`: SvelteKit app (UI + web API) and database schema (defined via Drizzle)
- `judge/`: Python judge worker and container for running submissions
- `problems/`: Problem metadata, Markdown explanations and test data files

## Installation

### Prerequisites

Tools you'll need to get up and running:
- [uv](https://docs.astral.sh/uv/getting-started/) to setup/manage the Python judge project
- [node 24](https://nodejs.org/en/download)
- [Docker](https://docs.docker.com/engine/install/) and [Docker compose](https://docs.docker.com/compose/install/)

### Setup

```sh
cp .env.example .env
# Fill in AUTH_SECRET and the GitHub OAuth values in .env (see comments in the file)

cd web
npm ci

cd ../judge
uv sync  # also installs Python 3.14 if you don't have it
```

For the GitHub `.env` values, [create an OAuth app](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) with the callback URL from `.env.example`.

## Running locally

From the repository root:

```sh
docker compose up   # Runs the Postgres DB and judge containers (needs its own terminal)

# In a separate shell
cd web
npm run db:setup    # Migrates the database and loads problem metadata
npm run dev         # Runs the web app, served at http://localhost:5173
```

## Updating the database schema

The database schema is defined in `web/src/lib/server/db/schema.ts`. After it's edited, you need to regenerate the database migrations (Drizzle generates a bunch of SQL for this) and then perform the actual migration on your local database instance.

```sh
npm run db:generate         # Generate database migrations
npm run db:migrate          # Apply migrations to local Postgres instance (must have run db:start)
npm run db:pymodels         # Regenerate Python models for sqlalchemy (judge/src/judge/queue/models.py)
```

The updated schema, the newly generated files in `web/drizzle`, and the updated Python models should all be committed together.

## Before opening a PR

If you updated anything in the web app: from `web/`, run `npm run check` and `npm run lint`.
