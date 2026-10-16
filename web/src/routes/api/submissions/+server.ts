import type { RequestHandler } from './$types';
import { notImplemented } from '#lib/server/notImplemented.ts';
import { json } from '@sveltejs/kit';

export const POST: RequestHandler =  async ({ locals }) => {
  const session = await locals.auth();

  if (!session) {
    return json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  return notImplemented();
};
