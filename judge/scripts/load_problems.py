"""
Loads metadata from problems/<slug>/ into the problems table in Postgres

Scans all subdirectories of `problems/` containing a `problem.toml` file. The entire
directory is hashed into the problem row's `content_hash`. Only `.in/.out` files under
the `data/` directory (plus the `[limits]` block in `problem.toml`) are considered for
the `data_hash`.

If the `content_hash` is changed, the problem is upserted.

Usage (from judge/): uv run python scripts/load_problems.py [--force]
The database instance must be running (start from web/).
"""

import hashlib
import json
import os
import sys
import tomllib
from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from judge.queue.models import Problems

PROBLEMS_DIR = Path(os.environ.get('PROBLEMS_DIR', Path(__file__).resolve().parents[2] / 'problems'))
DATABASE_URL = "postgresql+psycopg://" + os.environ['DATABASE_URL'].split('://', 1)[1]

# Whether to rewrite every row (e.g. after changing the loader script)
force = '--force' in sys.argv

with Session(create_engine(DATABASE_URL)) as session, session.begin():
    existing = dict(session.execute(select(Problems.slug, Problems.content_hash)).all())
    seen = set()
    rows = []

    for problem_dir in sorted(p for p in PROBLEMS_DIR.iterdir() if p.is_dir()):
        slug = problem_dir.name
        where = f"problems/{slug}/problem.toml"

        # Get all files in sorted order (for canonical hashing)
        files = sorted(
            p.relative_to(problem_dir).as_posix()
            for p in problem_dir.rglob("*")
            if p.is_file() and not any(part.startswith(".") for part in p.relative_to(problem_dir).parts)
        )

        # If there's no problem.toml, skip this directory
        if 'problem.toml' not in files:
            continue
        seen.add(slug)

        # Build content and data hashes for the current problem
        content_hash = hashlib.sha256()
        data_hash = hashlib.sha256()
        for file in files:
            data = (problem_dir / file).read_bytes()

            # Concatenate filename, nbytes and the actual data
            cur = f"{file}\0{len(data)}\0".encode() + data

            # Update the content hash
            content_hash.update(cur)
            # Update the data hash only if this is a test case input/output file
            if file.startswith('data/') and file.endswith(('.in', '.out')):
                data_hash.update(cur)

        # Get the content hash and check against its previous value
        # (if content hash is the same, data hash can't have changed)
        content = content_hash.hexdigest()
        if not force and existing.get(slug) == content:
            continue

        # Load the problem metadata
        toml = tomllib.loads((problem_dir / 'problem.toml').read_text())
        meta = toml.get("meta", {})

        # Validate problem metadata
        if not (
            all(isinstance(meta.get(key), str) for key in ('abbreviation', 'name', 'complexity')) and
            isinstance(meta.get('is_root', False), bool)
        ):
            raise ValueError(f"Problem `{where}`: [meta] block is invalid")

        # Get and validate shared and problem-specific limit values
        limits = toml.get('limits', {})
        sizes = limits.get('size', {}).values()
        if not (
            isinstance(limits.get('run', {}).get('time_ms'), int) and
            isinstance(limits.get('run', {}).get('memory_mb'), int)
        ):
            raise ValueError(f"{where}: [limits.run] block is invalid")
        if not all(
            isinstance(s, dict) and
            isinstance(s.get('input'), int) and
            isinstance(s.get('query'), int)
            for s in sizes
        ):
            raise ValueError(f"{where}: [limits.size] block is invalid")

        # Collect example JSON for the DB
        examples = []
        for input_path in sorted((problem_dir / 'data' / 'sample').glob('*.in')):
            output_path = input_path.with_suffix('.out')
            explanation_path = input_path.with_suffix('.md')
            examples.append({
                'name': input_path.stem,
                'input': input_path.read_text(),
                'output': output_path.read_text(),
                'explanation': explanation_path.read_text() if explanation_path.exists() else None,
            })

        # Update the data hash with problem limits
        data_hash.update(json.dumps(limits, sort_keys=True).encode())

        # Add the row for this problem to our batch
        rows.append({
            'slug': slug,
            'abbreviation': meta['abbreviation'],
            'name': meta['name'],
            'complexity': meta['complexity'],
            'is_root': meta.get('is_root', False),
            'time_limit_ms': limits['run']['time_ms'],
            'memory_limit_mb': limits['run']['memory_mb'],
            'size_limits': limits['size'],
            'statement': (problem_dir / 'statement.md').read_text(),
            'examples': examples,
            'content_hash': content,
            'data_hash': data_hash.hexdigest(),
        })

    # Update non-root problems first, so the new root doesn't break uniqueness check while
    # the old problem is still marked as root
    for row in sorted(rows, key=lambda r: r['is_root']):
        session.execute(
            insert(Problems)
            .values(row)
            .on_conflict_do_update(index_elements=[Problems.slug], set_={**row, 'updated_at': func.now()})
        )
        print(f"{'Updated' if row['slug'] in existing else 'Added'} {row['slug']}")

for slug in existing.keys() - seen:
    print(f'Problem "{slug}" is in the database but has no directory!', file=sys.stderr)
