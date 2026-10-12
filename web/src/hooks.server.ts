import { Auth } from '@auth/core';
import type { Session } from '@auth/core/types';
import type { Handle } from '@sveltejs/kit/hooks';
import { getAuthConfig } from './lib/server/auth';


export const handle: Handle = async ({ event, resolve }) => {
  const config = getAuthConfig();
  const pathname = event.url.pathname;

  if (pathname.startsWith('/auth/')) {
    return Auth(event.request, config);
  }

  let sessionPromise: Promise<Session | null> | undefined;
  const sessionCookies: string[] = [];

  event.locals.auth = () => {
    sessionPromise ??= readSession();
    return sessionPromise;
  };

  async function readSession(): Promise<Session | null> {
    const url = new URL('/auth/session', event.url.origin);

    const response = await Auth(
      new Request(url, {
        headers: {
          cookie: event.request.headers.get('cookie') ?? ''
        }
      }),
      config
    );

    sessionCookies.push(...response.headers.getSetCookie());

    if (!response.ok) {
      throw new Error('Unable to read authentication session');
    }

    const session = (await response.json()) as Session | null;

    return session?.user?.id ? session : null;
  }

  const response = await resolve(event);

  if (!sessionPromise) {
    return response;
  }

  await sessionPromise;

  const headers = new Headers(response.headers);

  for (const cookie of sessionCookies) {
    headers.append('set-cookie', cookie);
  }

  headers.set('cache-control', 'private, no-store');

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers
  });
};