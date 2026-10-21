# Problems

This directory is home to the problem definitions.

Each problem is defined by a directory with the following structure:

```
sat/
├── problem.toml      # metadata and bounds
├── statement.md      # statement shown to users
└── data/
    ├── sample/       # shown to users: 001.in, 001.out, optional 001.md explanation
    └── secret/       # hidden test cases: 001.in, 001.out
```

## After adding or changing a problem

Problem data is read from the database, not this directory. For changes to be visible in the web app, you'll need to reload the problems into Postgres. From the `web/` directory:

```sh
npm run db:start  # needs its own shell
npm run db:load-problems
```

Problems are upserted iff there is any change within their directory. If any `problem.toml` is invalid, nothing is written and the script will display an error message you can use to debug.

A problem's `data_hash` is updated by the loader if any test data changes (this counts all `.in`/`.out` files under `data/`, plus values in the metadata `[limits]` block). Judge runs record the data version they were tested against so verdicts may be invalidated by a change in problem data.

If you change the actual loader script (`judge/scripts/load_problems.py`), then run `npm run db:load-problems -- --force` to force rewriting every problem's row in the database.
