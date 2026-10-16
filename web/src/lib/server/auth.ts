import type { AuthConfig } from '@auth/core';
import Github from '@auth/core/providers/github';
import {
  GITHUB_CLIENT_ID,
  GITHUB_CLIENT_SECRET,
  AUTH_SECRET
} from '$app/env/private';

let config: AuthConfig | undefined;

export function getAuthConfig(): AuthConfig {
    if(config) return config;
    const clientId = GITHUB_CLIENT_ID;
    const clientSecret = GITHUB_CLIENT_SECRET;
    const secret = AUTH_SECRET;
    
    if(!clientId || !clientSecret || !secret) {
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
            jwt({ token, account }) {
                if (account?.provider === 'github') {
                    token.sub = `github:${account.providerAccountId}`;
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
