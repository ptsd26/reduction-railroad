# Python judge worker script

This directory is home to the Python judge script. One worker is a Docker container with an instance of the judge script and a single instance of isolate; the script pulls submissions from the judging queue and runs them through isolate in its container.

The `scripts` directory is not part of the main judge worker; it contains tooling such as a script to generate typed models from the migrated Postgres database. When the database schema is updated (from SvelteKit), to regenerate models:

```sh
cd web && npm run db:start  # if Postgres DB not already running

# In a separate terminal session
npm run db:migrate
npm run db:pymodels
```
