import os
import time
import traceback

from judge.runner import run_cpp
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from judge.queue.models import JudgeRunStatus, JudgeRuns, Verdict

# SQLAlchemy needs the driver in the URL scheme
engine = create_engine("postgresql+psycopg://" + os.environ["DATABASE_URL"].split("://", 1)[1])

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

        assert source is not None
        try:
            verdict, verdict_meta = judge(source, run_id)
        except Exception as e:
            traceback.print_exc()
            verdict = Verdict.FAILED
            verdict_meta = {'exception': str(e)}

        with Session(engine) as session, session.begin():
            run = session.get_one(JudgeRuns, run_id)

            if verdict == Verdict.FAILED:
                run.judge_attempts += 1
                if run.judge_attempts >= MAX_ATTEMPTS:
                    run.status = JudgeRunStatus.DONE
                    run.verdict = verdict
                    run.verdict_meta = verdict_meta
                    run.completed_at = func.now()
                else:
                    run.status = JudgeRunStatus.QUEUED
            else:
                run.status = JudgeRunStatus.DONE
                run.verdict = verdict
                run.verdict_meta = verdict_meta
                run.completed_at = func.now()
