import type { PageLoad } from './$types';
import type { ProblemsResponse } from '../api/problems/+server';
import { error } from '@sveltejs/kit';

export const load: PageLoad = async ({ fetch }) => {
    const res = await fetch('/api/problems');

    if (!res.ok) {
        error(res.status, 'Failed to load problems');
    }

    const problems: ProblemsResponse = await res.json();

    return { problems };
};
