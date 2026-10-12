import type { Handle } from '@sveltejs/kit/hooks';

const handleAuth: Handle = async ({ event, resolve }) => {
	// TODO: Handle authentication here
	return resolve(event);
};

export const handle: Handle = handleAuth;
