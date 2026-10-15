from typing import Optional
import datetime
import enum
import uuid

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Computed, DateTime, Enum, ForeignKeyConstraint, Identity, Index, Integer, PrimaryKeyConstraint, Table, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class JudgeRunStatus(str, enum.Enum):
    QUEUED = 'queued'
    RUNNING = 'running'
    DONE = 'done'


class Verdict(str, enum.Enum):
    ACCEPTED = 'accepted'
    WRONG_ANSWER = 'wrong_answer'
    COMPILE_ERROR = 'compile_error'
    RUNTIME_ERROR = 'runtime_error'
    TIME_LIMIT_EXCEEDED = 'time_limit_exceeded'
    MEMORY_LIMIT_EXCEEDED = 'memory_limit_exceeded'
    INVALID_QUERY = 'invalid_query'
    QUERY_LIMIT_EXCEEDED = 'query_limit_exceeded'
    QUERY_MISMATCH = 'query_mismatch'
    ORACLE_TIMEOUT = 'oracle_timeout'
    INVALID_WITNESS = 'invalid_witness'
    FAILED = 'failed'


t_judge_run_results = Table(
    'judge_run_results', Base.metadata,
    Column('id', BigInteger),
    Column('submission_id', BigInteger),
    Column('status', Enum(JudgeRunStatus, values_callable=lambda cls: [member.value for member in cls], name='judge_run_status')),
    Column('created_at', DateTime(True)),
    Column('verdict', Enum(Verdict, values_callable=lambda cls: [member.value for member in cls], name='verdict')),
    Column('metric_max_output_size', Integer),
    Column('metric_max_runtime_ms', Integer),
    Column('code_nbytes', Integer)
)


class Problems(Base):
    __tablename__ = 'problems'
    __table_args__ = (
        PrimaryKeyConstraint('slug', name='problems_pkey'),
        Index('problems_unique_root', 'is_root', postgresql_where='is_root', unique=True)
    )

    slug: Mapped[str] = mapped_column(Text, primary_key=True)
    abbreviation: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    complexity: Mapped[str] = mapped_column(Text, nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    examples: Mapped[object] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    is_root: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    data_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))

    submissions_from_problem: Mapped[list['Submissions']] = relationship('Submissions', foreign_keys='[Submissions.from_problem]', back_populates='problems')
    submissions_to_problem: Mapped[list['Submissions']] = relationship('Submissions', foreign_keys='[Submissions.to_problem]', back_populates='problems_')


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='users_pkey'),
        UniqueConstraint('github_id', name='users_github_id_unique')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    github_id: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)

    submissions: Mapped[list['Submissions']] = relationship('Submissions', back_populates='user')


class Submissions(Base):
    __tablename__ = 'submissions'
    __table_args__ = (
        CheckConstraint('from_problem <> to_problem', name='submissions_distinct_problems'),
        ForeignKeyConstraint(['from_problem'], ['problems.slug'], name='submissions_from_problem_problems_slug_fk'),
        ForeignKeyConstraint(['to_problem'], ['problems.slug'], name='submissions_to_problem_problems_slug_fk'),
        ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', name='submissions_user_id_users_id_fk'),
        PrimaryKeyConstraint('id', name='submissions_pkey'),
        Index('submissions_edge', 'from_problem', 'to_problem'),
        Index('submissions_user_edge', 'user_id', 'from_problem', 'to_problem')
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    from_problem: Mapped[str] = mapped_column(Text, nullable=False)
    to_problem: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    code_nbytes: Mapped[Optional[int]] = mapped_column(Integer, Computed('octet_length(source)', persisted=True))

    problems: Mapped['Problems'] = relationship('Problems', foreign_keys=[from_problem], back_populates='submissions_from_problem')
    problems_: Mapped['Problems'] = relationship('Problems', foreign_keys=[to_problem], back_populates='submissions_to_problem')
    user: Mapped['Users'] = relationship('Users', back_populates='submissions')
    judge_runs: Mapped[list['JudgeRuns']] = relationship('JudgeRuns', back_populates='submission')


class JudgeRuns(Base):
    __tablename__ = 'judge_runs'
    __table_args__ = (
        ForeignKeyConstraint(['submission_id'], ['submissions.id'], ondelete='CASCADE', name='judge_runs_submission_id_submissions_id_fk'),
        PrimaryKeyConstraint('id', name='judge_runs_pkey'),
        Index('judge_runs_queue', 'created_at', postgresql_where="(status = ANY (ARRAY['queued'::judge_run_status, 'running'::judge_run_status]))"),
        Index('judge_runs_submission', 'submission_id', 'created_at')
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True, start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    test_data_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    status: Mapped[JudgeRunStatus] = mapped_column(Enum(JudgeRunStatus, values_callable=lambda cls: [member.value for member in cls], name='judge_run_status'), nullable=False, server_default=text("'queued'::judge_run_status"))
    judge_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    current_case: Mapped[Optional[int]] = mapped_column(Integer)
    total_cases: Mapped[Optional[int]] = mapped_column(Integer)
    verdict: Mapped[Optional[Verdict]] = mapped_column(Enum(Verdict, values_callable=lambda cls: [member.value for member in cls], name='verdict'))
    verdict_meta: Mapped[Optional[object]] = mapped_column(JSONB)
    metric_max_output_size: Mapped[Optional[int]] = mapped_column(Integer)
    metric_max_runtime_ms: Mapped[Optional[int]] = mapped_column(Integer)
    judge_worker_id: Mapped[Optional[str]] = mapped_column(Text)
    judge_lease_expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))

    submission: Mapped['Submissions'] = relationship('Submissions', back_populates='judge_runs')
