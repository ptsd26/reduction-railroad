import { json } from '@sveltejs/kit';

export function notImplemented() {
	return json(
		{ error: { code: 'NOT_IMPLEMENTED', message: 'This API endpoint is a placeholder.' } },
		{ status: 501, headers: { 'Cache-Control': 'no-store' } }
	);
}
