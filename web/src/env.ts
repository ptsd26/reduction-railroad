import { defineEnvVars } from '@sveltejs/kit/env';

export const variables = defineEnvVars({
	ORIGIN: { description: 'The app origin (base URL), e.g. `http://localhost:5173`.' },
	DATABASE_URL: { description: 'The database connection string.' },
	AUTH_SECRET: { description: 'Secret used to encrypt the session cookie. Generate with `openssl rand -base64 33`.' },
	GITHUB_CLIENT_ID: { description: 'Client ID for GitHub OAuth app.' },
	GITHUB_CLIENT_SECRET: { description: 'Client secret for the GitHub OAuth app.' },
});
