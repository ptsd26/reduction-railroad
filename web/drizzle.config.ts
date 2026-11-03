import { defineConfig } from 'drizzle-kit';
import { loadEnv } from 'vite';

const { DATABASE_URL } = loadEnv('development', '..', '');
if (!DATABASE_URL) throw new Error('DATABASE_URL is not set');

export default defineConfig({
	schema: './src/lib/server/db/schema.ts',
	dialect: 'postgresql',
	dbCredentials: { url: DATABASE_URL },
	verbose: true,
	strict: true
});
