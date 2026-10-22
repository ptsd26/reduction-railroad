
import argparse
import sys
from pathlib import Path

from judge.runner import run_cpp


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile and run a C++ submission in Isolate."
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Path to the C++ source file to judge",
    )
    args = parser.parse_args()

    if not args.source.is_file():
        parser.error(f"source file not found: {args.source}")

    try:
        result = run_cpp(args.source)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    if result.compile_stdout:
        print(result.compile_stdout, end="")

    if result.compile_stderr:
        print(result.compile_stderr, end="", file=sys.stderr)

    if result.stdout:
        print(result.stdout, end="")

    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.timed_out:
        raise SystemExit("Compilation or execution timed out")

    if result.exit_code != 0:
        raise SystemExit(result.exit_code or 1)


if __name__ == "__main__":
    main()
