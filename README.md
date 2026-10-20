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

Currently Docker compose is used within the web directory, but we'll eventually move that to a root-level compose setup to easily spin up the whole deployment.

### Setup

```sh
cd web
cp .env.example .env
# Fill in AUTH_SECRET and the GitHub OAuth values in .env (see comments in the file)
npm ci

cd ../judge
uv sync  # also installs Python 3.14 if you don't have it
```

For the GitHub `.env` values, [create an OAuth app](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app) with the callback URL from `.env.example`.

## Running locally

From `web/`:

```sh
npm run db:start    # Runs the Postgres container in the foreground (needs its own terminal)
npm run db:migrate  # Create/update tables; re-run after schema is changed
npm run dev         # http://localhost:5173
```

## Updating the database schema

The database schema is defined in `web/src/lib/server/db/schema.ts`. After it's edited, you need to regenerate the database migrations (Drizzle generates a bunch of SQL for this) and then perform the actual migration on your local database instance.

```sh
npm run db:generate   # Generate database migrations
npm run db:migrate    # Apply migrations to local Postgres instance (must have run db:start)
npm run db:pymodels   # Regenerate Python models for sqlalchemy (judge/src/judge/queue/models.py)
```

The updated schema, the newly generated files in `web/drizzle`, and the updated Python models should all be committed together.

## Before opening a PR

If you updated anything in the web app: from `web/`, run `npm run check` and `npm run lint`.
