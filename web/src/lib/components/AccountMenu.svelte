<script lang="ts">
  import type { Session } from "@auth/core/types";
  import { refreshAll } from "$app/navigation";
  import LogOutIcon from "@lucide/svelte/icons/log-out";
  import * as DropdownMenu from "#lib/components/ui/dropdown-menu/index.ts";
  import { Button } from "#lib/components/ui/button/index.ts";

  // Get the user session
  let { user }: { user: Session['user'] | null } = $props();

  /**
   * Helper to POST to some auth endpoint
  */
  async function doAuthPost(action: 'signin/github' | 'signout'): Promise<string> {
    // Fetching /auth/csrf sets the CSRF cookie for Auth.js; this cookie
    // must match the CSRF token we provide in the auth request.
    const { csrfToken } = await (await fetch('/auth/csrf')).json();

    const res = await fetch(`/auth/${action}`, {
      method: 'POST',
      headers: { 'X-Auth-Return-Redirect': "1" },
      body: new URLSearchParams({ csrfToken }),
    });
    return (await res.json()).url;
  }

  async function signIn() {
    // Redirect to the GitHub signin page
    window.location.href = await doAuthPost('signin/github');
  }

  async function signOut() {
    // Sign out and refresh state since there will no longer be a session
    await doAuthPost("signout");
    await refreshAll();
  }
</script>

{#if user}
  <DropdownMenu.Root>
    <DropdownMenu.Trigger class="rounded-full cursor-pointer">
      <img src={user.image} alt={user.name} class="size-12 rounded-full" />
    </DropdownMenu.Trigger>

    <DropdownMenu.Content align="end" class="min-w-48">
      <DropdownMenu.Label>Signed in as <b>{user.name}</b></DropdownMenu.Label>
      <DropdownMenu.Separator />

      <DropdownMenu.Item onSelect={signOut}>
        <LogOutIcon />
        Sign out
      </DropdownMenu.Item>
    </DropdownMenu.Content>
  </DropdownMenu.Root>
{:else}
  <Button onclick={signIn}>Sign in with GitHub</Button>
{/if}
