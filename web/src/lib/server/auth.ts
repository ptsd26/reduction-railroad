import type { AuthConfig } from '@auth/core';
import Github from '@auth/core/providers/github';
import {
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    AUTH_SECRET
} from '$app/env/private';
import { db } from './db';
import { users } from './db/schema';
import { sql } from 'drizzle-orm';

let config: AuthConfig | undefined;

export function getAuthConfig(): AuthConfig {
    if (config) return config;
    const clientId = GITHUB_CLIENT_ID;
    const clientSecret = GITHUB_CLIENT_SECRET;
    const secret = AUTH_SECRET;

    if (!clientId || !clientSecret || !secret) {
        throw new Error('Missing env variable for auth config');
    }

    config = {
        basePath: '/auth',
        secret,
        trustHost: true,

        providers: [
            Github({
                clientId,
                clientSecret
            })
        ],

        session: {
            strategy: 'jwt',
            maxAge: 30 * 24 * 60 * 60 // 30 days
        },

        callbacks: {
            async jwt({ token, account, profile, user }) {
                if (account?.provider === 'github') {
                    // Insert or update the user in the DB
                    const [row] = await db.insert(users)
                        .values({
                            githubId: account.providerAccountId,
                            username: String(profile?.login),
                            avatarUrl: user.image
                        })
                        .onConflictDoUpdate({
                            target: users.githubId,
                            set: {
                                // `excluded.x` is the value of x we provided in our insert statement above
                                username: sql`excluded.username`,
                                avatarUrl: sql`excluded.avatar_url`
                            }
                        })
                        .returning({ id: users.id, username: users.username });
                    token.sub = row.id;
                    token.name = row.username;
                }

                return token;
            },

            session({ session, token }) {
                if (session.user && token.sub) {
                    session.user.id = token.sub;
                }

                return session;
            }
        }
    };

    return config;
}
