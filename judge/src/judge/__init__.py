import os
import time
import traceback
import socket

from judge.runner import run_cpp
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from judge.queue.models import JudgeRunStatus, JudgeRuns, Verdict

# Id of this judge worker box
WORKER_ID = socket.gethostname()

# Max number of attempts to judge a solution before it counts as failed
MAX_ATTEMPTS = 3


def judge(source: str, run_id: int) -> tuple[Verdict, dict]:
    result = run_cpp(source)

    # No exit code if compile error or ran out of time
    if result.timed_out:
        return Verdict.TIME_LIMIT_EXCEEDED, {}

    if result.exit_code is None:  # compile failed
        return Verdict.COMPILE_ERROR, {'stderr': result.compile_stderr}

    if result.exit_code != 0:
        return Verdict.RUNTIME_ERROR, {}

    if result.stdout.strip().lower() == 'hello, world!':
        return Verdict.ACCEPTED, {}

    return Verdict.WRONG_ANSWER, {}


def main() -> None:
    # SQLAlchemy needs the driver in the URL scheme
    engine = create_engine("postgresql+psycopg://" + os.environ["DATABASE_URL"].split("://", 1)[1])

    while True:
        # Find oldest queued run that's not currently locked by another worker
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
                # Claim the run
                run.status = JudgeRunStatus.RUNNING
                run.current_case = 1
                run.total_cases = 1
                run.judge_worker_id = WORKER_ID

                run_id = run.id
                source = run.submission.source

        if run_id is None:
            time.sleep(1)
            continue

        # Try to judge the source file
        assert source is not None
        try:
            verdict, verdict_meta = judge(source, run_id)
        except Exception as e:
            traceback.print_exc()
            verdict = Verdict.FAILED
            verdict_meta = {'exception': str(e)}

        with Session(engine) as session, session.begin():
            run = session.get_one(JudgeRuns, run_id)

            # A run can fail MAX_ATTEMPTS times before we give it the FAILED verdict
            if verdict == Verdict.FAILED:
                run.judge_attempts += 1
                if run.judge_attempts >= MAX_ATTEMPTS:
                    run.status = JudgeRunStatus.DONE
                    run.verdict = verdict
                    run.verdict_meta = verdict_meta
                    run.completed_at = func.now()
                else:
                    # Hasn't failed enough times to be counted as failed; retry
                    run.status = JudgeRunStatus.QUEUED
            else:
                run.status = JudgeRunStatus.DONE
                run.verdict = verdict
                run.verdict_meta = verdict_meta
                run.completed_at = func.now()
