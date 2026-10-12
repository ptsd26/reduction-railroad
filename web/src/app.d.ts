import type { Session } from '@auth/core/types';

declare global {
  namespace App {
    interface Locals {
      auth: () => Promise<Session | null>;
    }
  }
}

export {};