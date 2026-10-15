#!/usr/bin/env sh
# Regenerates src/judge/queue/models.py from the migrated database schema.
# Run after applying migrations (`npm run db:migrate` in web/).
# Uses DATABASE_URL if set, otherwise the local compose DB.
set -eu
cd "$(dirname "$0")/.."

url="${DATABASE_URL:-postgres://root:mysecretpassword@localhost:5432/local}"
url="postgresql+psycopg://${url#*://}" # SQLAlchemy needs driver in the URL scheme

uv run sqlacodegen --generator declarative "$url" --outfile src/judge/queue/models.py
echo "Wrote src/judge/queue/models.py"
