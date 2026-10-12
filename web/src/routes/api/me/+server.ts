import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ locals }) => {
  const session = await locals.auth();

  if (!session) {
    return json(
      { error: 'Unauthorized' },
      { status: 401 }
    );
  }

  return json({
    user: {
      id: session.user.id,
      name: session.user.name,
      email: session.user.email,
      image: session.user.image
    }
  });
};