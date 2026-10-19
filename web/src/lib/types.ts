/**
 * Describes the status of a judge run (may be multiple per submission).
 */
export const JudgeRunStatus = {
    QUEUED: 'queued',
    RUNNING: 'running',
    DONE: 'done',
} as const;
export type JudgeRunStatus = (typeof JudgeRunStatus)[keyof typeof JudgeRunStatus]

/**
 * Describes a verdict for a judge run.
 *
 * The verdict of a user submission is the verdict assigned to its latest judge run
 * (thus in the event of rejudging, a verdict may be reassigned to a submission).
 */
export const Verdict = {
    ACCEPTED: 'accepted',
    WRONG_ANSWER: 'wrong_answer',
    COMPILE_ERROR: 'compile_error',
    RUNTIME_ERROR: 'runtime_error',
    TIME_LIMIT_EXCEEDED: 'time_limit_exceeded',
    MEMORY_LIMIT_EXCEEDED: 'memory_limit_exceeded',
    INVALID_QUERY: 'invalid_query', // query malformed
    QUERY_LIMIT_EXCEEDED: 'query_limit_exceeded', // query too large, or multiple queries
    QUERY_MISMATCH: 'query_mismatch', // query didn't match on the second run (nondeterministic?)
    ORACLE_TIMEOUT: 'oracle_timeout', // oracle didn't answer the query in time (oops)
    INVALID_WITNESS: 'invalid_witness', // decision correct, but witness is malformed or incorrect
    FAILED: 'failed', // judging failed multiple times; something's wrong!
} as const;
export type Verdict = (typeof Verdict)[keyof typeof Verdict]

/**
 * Describes a sample case with input/output and optional explanation Markdown.
 */
export type Example = {
    name: string;
    input: string;
    output: string;
    explanation: string | null;
};
