import { JudgeRunStatus, SizeLimits, Verdict, type Example } from '#lib/types.ts';
import { eq, sql } from 'drizzle-orm';
import {
	bigint,
	boolean,
	check,
	index,
	integer,
	jsonb,
	pgEnum,
	pgTable,
	pgView,
	text,
	timestamp,
	uniqueIndex,
	uuid
} from 'drizzle-orm/pg-core';

/**
 * Judged run status enum
 */
export const judgeRunStatus = pgEnum('judge_run_status', JudgeRunStatus);

/**
 * Judged run/submission verdict enum
 */
export const verdict = pgEnum('verdict', Verdict);

/**
 * Constructs a timestamp with an attached timezone.
 */
const timestamptz = (name: string) => timestamp(name, { withTimezone: true });

/**
 * User table.
 * Primary key is a unique ID into the table we generate; GitHub ID is only a column.
 */
export const users = pgTable('users', {
	id: uuid('id').primaryKey().defaultRandom(), // random UUID assigned on creation
	githubId: text('github_id').notNull().unique(),
	username: text('username').notNull(),
	avatarUrl: text('avatar_url'),
	createdAt: timestamptz('created_at').notNull().defaultNow(),
});

/**
 * Table of problem metadata, read at startup from the static `problems/` directory
 */
export const problems = pgTable(
	'problems',
	{
		// Identifying information
		slug: text('slug').primaryKey(),
		abbreviation: text('abbreviation').notNull(),
		name: text('name').notNull(),
		complexity: text('complexity').notNull(),
		statement: text('statement').notNull(),
		examples: jsonb('examples').$type<Example[]>().notNull().default([]),
		isRoot: boolean('is_root').notNull().default(false),

		// Run and problem bounds
		timeLimitMs: integer('time_limit_ms').notNull().default(1000),
		memoryLimitMb: integer('memory_limit_mb').notNull().default(256),
		sizeLimits: jsonb('size_limits').$type<SizeLimits>().notNull(), // problem-specific size limits for input and query instances

		// Hashes and timestamps for detecting changes to the problem directory and judge data
		contentHash: text('content_hash').notNull(), // full problem directory hash
		dataHash: text('data_hash').notNull(), // only judge data that could impact a verdict
		createdAt: timestamptz('created_at').notNull().defaultNow(),
		updatedAt: timestamptz('updated_at').notNull().defaultNow(), // set by the loader script when content_hash changes
	},
	(t) => [
		// Require a unique problem graph root
		uniqueIndex('problems_unique_root').on(t.isRoot).where(sql`${t.isRoot}`),
	]
);

/**
 * Submission table; one entry per user-submitted code file
 */
export const submissions = pgTable(
	'submissions',
	{
		id: bigint('id', { mode: 'number' })
			.primaryKey()
			.generatedAlwaysAsIdentity(),
		userId: uuid('user_id')
			.notNull()
			.references(() => users.id, { onDelete: 'cascade' }),
		fromProblem: text('from_problem')
			.notNull()
			.references(() => problems.slug),
		toProblem: text('to_problem')
			.notNull()
			.references(() => problems.slug),
		source: text('source').notNull(),
		codeNbytes: integer('code_nbytes').generatedAlwaysAs(sql`octet_length(source)`),
		createdAt: timestamptz('created_at').notNull().defaultNow(),
	},
	(t) => [
		// Require that a reduction be between two different problems
		check('submissions_distinct_problems', sql`${t.fromProblem} <> ${t.toProblem}`),
		// Allow indexing submissions by user and reduction edge
		index('submissions_user_edge').on(t.userId, t.fromProblem, t.toProblem),
		// Allow indexing submissions by reduction edge
		index('submissions_edge').on(t.fromProblem, t.toProblem),
	]
);

/**
 * Judge runs; >=1 entry per submission (new runs may be spawned by rejudge or otherwise)
 */
export const judgeRuns = pgTable(
	'judge_runs',
	{
		// Identifying information
		id: bigint('id', { mode: 'bigint' })
			.primaryKey()
			.generatedAlwaysAsIdentity(), // sequential ID incrementing with each row
		submissionId: bigint('submission_id', { mode: 'number' })
			.notNull()
			.references(() => submissions.id, { onDelete: 'cascade' }),
		testDataVersion: text('test_data_version').notNull(), // `${from.data_hash}:${to.data_hash}`
		createdAt: timestamptz('created_at').notNull().defaultNow(),

		// Judge run state
		status: judgeRunStatus('status').notNull().default('queued'),
		currentCase: integer('current_case'), // case currently being tested
		totalCases: integer('total_cases'), // total number of cases the run is being tested on
		judgeAttempts: integer('judge_attempts').notNull().default(0), // number of times this run has failed
		judgeWorkerId: text('judge_worker_id'),
		judgeLeaseExpiresAt: timestamptz('judge_lease_expires_at'),
		completedAt: timestamptz('completed_at'),

		// Verdict and metrics (may be null if the run is not yet complete)
		verdict: verdict('verdict'),
		verdictMeta: jsonb('verdict_meta'),
		metricMaxOutputSize: integer('metric_max_output_size'),
		metricMaxRuntimeMs: integer('metric_max_runtime_ms'),
	},
	(t) => [
		// Allow indexing by latest run on a given submission (for submission verdict)
		index('judge_runs_submission').on(t.submissionId, t.createdAt.desc()),
		// Allow filtering to queued or currently running
		index('judge_runs_queue')
			.on(t.createdAt)
			.where(sql`${t.status} in ('queued', 'running')`),
	]
);

/**
 * Shorthand for querying judge run metrics
 */
export const runMetrics = {
	maxOutputSize: judgeRuns.metricMaxOutputSize,
	maxRuntimeMs: judgeRuns.metricMaxRuntimeMs,
	codeNbytes: submissions.codeNbytes,
}

/**
 * Shorthand for querying judge run limits
 */
export const runLimits = {
	timeMs: problems.timeLimitMs,
	memoryMb: problems.memoryLimitMb,
};

/**
 * Prebuilt view for querying judge run results with verdict and metrics
 */
export const judgeRunResults = pgView('judge_run_results').as((qb) =>
	qb
		.select({
			id: judgeRuns.id,
			submissionId: judgeRuns.submissionId,
			status: judgeRuns.status,
			createdAt: judgeRuns.createdAt,
			verdict: judgeRuns.verdict,
			metricMaxOutputSize: judgeRuns.metricMaxOutputSize,
			metricMaxRuntimeMs: judgeRuns.metricMaxRuntimeMs,
			metricCodeNbytes: submissions.codeNbytes
		})
		.from(judgeRuns)
		.innerJoin(submissions, eq(submissions.id, judgeRuns.submissionId))
);
