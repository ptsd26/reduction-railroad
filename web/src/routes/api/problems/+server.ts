import type { RequestHandler } from './$types';
import { json } from '@sveltejs/kit';

/**
 * Describes the response from the problems GET endpoint.
*/
export type ProblemsResponse = {
    slugs: string[];
}

export const GET: RequestHandler = async () => {
    return json({ slugs : ["sat", "clique"] } satisfies ProblemsResponse, { status: 200});
};