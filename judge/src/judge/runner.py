import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path


BOX_ROOT = Path("/var/lib/isolate")
MAX_SOURCE_BYTES = 64 * 1024


@dataclass
class RunResult:
    stdout: str
    stderr: str
    compile_stdout: str
    compile_stderr: str
    exit_code: int | None
    timed_out: bool = False


def _command(
    args: list[str], timeout: int
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def run_cpp(source: string) -> RunResult:
    """Compile and execute a C++ source file inside an Isolate sandbox."""

    if not source:
        raise ValueError("C++ source is required")
    if len(source) > MAX_SOURCE_BYTES:
        raise ValueError("Source too large")
    
    box_id = uuid.uuid4().int % 1_000
    initialized = False

    try:
        init = _command(
            ["isolate", "--box-id", str(box_id), "--init"],
            timeout=5,
        )
        if init.returncode != 0:
            return RunResult(
                stdout="",
                stderr=init.stderr.decode("utf-8", errors="replace"),
                compile_stdout="",
                compile_stderr="Could not initialize Isolate",
                exit_code=None,
            )

        initialized = True
        box = BOX_ROOT / str(box_id) / "box"
        (box / "main.cpp").write_bytes(source)

        try:
            compiled = _command(
                [
                    "isolate", "--box-id", str(box_id),
                    "--time", "10", "--wall-time", "15",
                    "--mem", "262144", "--fsize", "1024",
                    "--processes=64", "--env=PATH", "--run", "--",
                    "/usr/bin/g++", "-std=c++17", "-O2",
                    "main.cpp", "-o", "main",
                ],
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            return RunResult("", "", "", "Compilation timed out", None, True)

        compile_stdout = compiled.stdout.decode("utf-8", errors="replace")
        compile_stderr = compiled.stderr.decode("utf-8", errors="replace")

        if compiled.returncode != 0:
            for filename in ("stdout", "stderr"):
                output_file = box / filename
                if output_file.exists():
                    content = output_file.read_text(errors="replace")
                    if filename == "stdout":
                        compile_stdout += content
                    else:
                        compile_stderr += content

            return RunResult(
                "", "", compile_stdout, compile_stderr,
                compiled.returncode,
            )

        try:
            result = _command(
                [
                    "isolate", "--box-id", str(box_id),
                    "--time", "5", "--wall-time", "8",
                    "--mem", "262144", "--fsize", "1024",
                    "--processes=64", "--env=PATH", "--run", "--",
                    "./main",
                ],
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            return RunResult(
                "", "Execution timed out", compile_stdout,
                compile_stderr, None, True,
            )

        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")

        for filename in ("stdout", "stderr"):
            output_file = box / filename
            if output_file.exists():
                content = output_file.read_text(errors="replace")
                if filename == "stdout":
                    stdout = content
                else:
                    stderr = content

        return RunResult(
            stdout, stderr, compile_stdout, compile_stderr,
            result.returncode,
        )
    finally:
        if initialized:
            try:
                _command(
                    ["isolate", "--box-id", str(box_id), "--cleanup"],
                    timeout=5,
                )
            except (subprocess.TimeoutExpired, OSError):
                pass


import os
import time

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from judge.queue.models import JudgeRunStatus, JudgeRuns, Verdict

# SQLAlchemy needs the driver in the URL scheme
engine = create_engine("postgresql+psycopg://" + os.environ["DATABASE_URL"].split("://", 1)[1])


def judge(source: str, run_id: int) -> (Verdict, str):
    result = run_cpp(source)
    if result.exit_code == 0: return (Verdict.ACCEPTED, result.stdout)
    else: return (Vertict.RUNTIME_ERROR, result.stdout)


def main() -> None:
    while True:
        # Claim the oldest queued run, skipping any another worker is claiming right now
        with Session(engine) as session, session.begin():
            run = session.scalars(
                select(JudgeRuns)
                .where(JudgeRuns.status == JudgeRunStatus.QUEUED)
                .order_by(JudgeRuns.created_at)
                .limit(1)
                .with_for_update(skip_locked=True)
            ).first()
            if run is None:
                run_id = None
                source = None
            else:
                run.status = JudgeRunStatus.RUNNING
                run_id = run.id
                source = run.submission.source

        if run_id is None:
            time.sleep(1)
            continue

        
        verdict, result = judge(source, run_id)

        with Session(engine) as session, session.begin():
            run = session.get(JudgeRuns, run_id)
            run.status = JudgeRunStatus.DONE
            run.verdict = verdict
            run.verdict_meta = {"stdout": result}
            run.completed_at = func.now()
