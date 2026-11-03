import type { RequestHandler } from './$types';
import { json } from '@sveltejs/kit';
import { judgeRuns, problems, submissions, users } from '#lib/server/db/schema.ts';
import { and, eq, gt, inArray, sql } from 'drizzle-orm';
import { db } from '#lib/server/db/index.ts';

/**
 * Describes the request body for the submission POST endpoint.
 */
export type SubmitRequest = {
  fromProblem: string;
  toProblem: string;
  source: string; //source code
}

/**
 * Describes the response from the submission POST endpoint.
 */
export type SubmitResponse = {
  id: number;
}

/**
 * Posts a new submission to the server for judging.
 *
 * The server returns a submission ID that can be used to poll the status
 * or connect to an SSE stream for real-time judging updates.
 */
export const POST: RequestHandler = async ({ locals, request }) => {
  const session = await locals.auth();
  if (!session) {
    return json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  // Validate and retrieve request body
  const body = await request.json().catch(() => null);
  if (typeof body?.fromProblem !== 'string' || typeof body?.toProblem !== 'string' || typeof body?.source !== 'string') {
    return json({ error: 'Expected fromProblem, toProblem and source strings' }, { status: 400 });
  }
  const { fromProblem, toProblem, source }: SubmitRequest = body;

  // Look up the problems in the reduction
  const found = await db
    .select({ slug: problems.slug, dataHash: problems.dataHash })
    .from(problems)
    .where(inArray(problems.slug, [fromProblem, toProblem]));
  const from = found.find((p) => p.slug === fromProblem);
  const to = found.find((p) => p.slug === toProblem);

  // Validate the problems
  if (!from) { return json({ error: `Unknown problem ${fromProblem}` }, { status: 400 }); }
  if (!to) { return json({ error: `Unknown problem ${toProblem}` }, { status: 400 }); }
  if (from === to) { return json({ error: 'Reduced problem IDs must be distinct' }, { status: 400 }); }

  return await db.transaction(async (tx) => {
    // Lock the user row for this check/submission
    await tx
      .select({ id: users.id })
      .from(users)
      .where(eq(users.id, session.user.id))
      .for('update'); // locked "for updating"


    // Check for a recent submission from the same user to prevent spam
    const [recent] = await tx
      // Find submission IDs
      .select({ id: submissions.id })
      .from(submissions)
      // Filter for submissions from this user in the last 5 seconds
      .where(and(
        eq(submissions.userId, session.user.id),
        gt(submissions.createdAt, sql`now() - interval '5 seconds'`)
      ))
      // We only care whether there is at least one such submission
      .limit(1);

    // If there is a recent submission, reject this one
    if (recent) return json({ error: 'Slow down! Please wait before submitting again.' }, { status: 429 });

    // Otherwise, no recent submission; insert the new one
    const [submission] = await tx
      .insert(submissions)
      .values({ userId: session.user.id, fromProblem, toProblem, source })
      .returning({ id: submissions.id });

    // Place a run for this submission in the judge queue
    await tx.insert(judgeRuns).values({
      submissionId: submission.id,
      testDataVersion: `${from.dataHash}:${to.dataHash}`, // data version depends on both from/to hashes
    });
    await tx.execute(sql`notify judge_queue`);

    return json({ id: submission.id } satisfies SubmitResponse, { status: 201 });
  });
};
