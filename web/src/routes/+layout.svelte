<script lang="ts">
	import '../app.css';
	import favicon from '#lib/assets/favicon.svg';
	import AccountMenu from '#lib/components/AccountMenu.svelte';

	let { data, children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<!-- Navbar with the user/auth menu -->
<nav class="flex justify-end px-3 py-3 sm:px-5 sm:py-5">
	<AccountMenu user={data.user} />
</nav>

{@render children()}
