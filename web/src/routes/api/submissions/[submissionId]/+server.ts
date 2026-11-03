import { db } from '#lib/server/db/index.ts';
import { judgeRuns, runMetrics, submissions } from '#lib/server/db/schema.ts';
import type { JudgeRunStatus, Verdict } from '#lib/types.ts';
import { and, desc, eq } from 'drizzle-orm';
import type { RequestHandler } from './$types';

/**
 * Describes the response from the submissions GET endpoint.
 * Run-related fields are populated from the submission's latest judge run.
 */
export type GetSubmissionResponse = {
  // Submission metadata
  id: number;
  fromProblem: string;
  toProblem: string;
  source: string;
  createdAt: string; // ISO timestamp returned as a string

  // Current/total cases are null until the run is started
  status: JudgeRunStatus;
  currentCase: number | null;
  totalCases: number | null;

  // These fields are null until the run is done
  verdict: Verdict | null;
  verdictMeta: Record<string, unknown> | null;
  completedAt: string | null; // ISO timestamp returned as a string
  metrics: {
    maxRuntimeMs: number | null;
    maxOutputSize: number | null;
    codeNbytes: number | null;
  };
};

/**
 * This endpoint fetches a submission owned by the authenticated user,
 * returning all associated metadata + the latest judge run status, verdict, and metrics.
 */
export const GET: RequestHandler = async ({ locals, params }) => {
  const session = await locals.auth();
  if (!session) return Response.json(
    { error: "Unauthorized" },
    { status: 401 }
  );

  // Parse the submission ID from the route params and ensure it's a number
  const id = Number(params.submissionId);
  if (!Number.isSafeInteger(id)) return Response.json(
    { error: `Invalid submission ID ${params.submissionId}` },
    { status: 400 }
  );

  // Fetch the submission and its latest judge run
  const [row] = await db
    .select({
      id: submissions.id,
      fromProblem: submissions.fromProblem,
      toProblem: submissions.toProblem,
      source: submissions.source,
      createdAt: submissions.createdAt,

      status: judgeRuns.status,
      currentCase: judgeRuns.currentCase,
      totalCases: judgeRuns.totalCases,

      verdict: judgeRuns.verdict,
      verdictMeta: judgeRuns.verdictMeta,
      completedAt: judgeRuns.completedAt,
      metrics: runMetrics,
    })
    .from(submissions)
    .innerJoin(judgeRuns, eq(judgeRuns.submissionId, submissions.id))
    .where(and(
      eq(submissions.id, id),
      eq(submissions.userId, session.user.id), // only the owner can see their submission
    ))
    .orderBy(desc(judgeRuns.createdAt))
    .limit(1);

  // Return a 404 if the submission doesn't exist or isn't owned by the user
  if (!row) return Response.json(
    { error: "Submission not found" },
    { status: 404 }
  );

  // Otherwise return the submission and associated run data
  return Response.json({
    id: row.id,
    fromProblem: row.fromProblem,
    toProblem: row.toProblem,
    source: row.source,
    createdAt: row.createdAt.toISOString(),

    status: row.status,
    currentCase: row.currentCase,
    totalCases: row.totalCases,

    verdict: row.verdict,
    verdictMeta: row.verdictMeta,
    completedAt: row.completedAt?.toISOString() ?? null,
    metrics: {
      maxRuntimeMs: row.metrics.maxRuntimeMs,
      maxOutputSize: row.metrics.maxOutputSize,
      codeNbytes: row.metrics.codeNbytes,
    },
  } satisfies GetSubmissionResponse);
};
