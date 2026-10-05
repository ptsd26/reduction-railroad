<script>
	import CodeEditor from '#lib/CodeEditor.svelte';
</script>

<svelte:head>
	<title>Reduction Railroad | Frontend demo</title>
	<meta name="description" content="A minimal Reduction Railroad frontend demo with a C++ editor." />
</svelte:head>

<main class="mx-auto max-w-6xl px-4 py-10 sm:px-8">
	<header class="mb-8">
		<p class="mb-2 text-sm font-semibold uppercase tracking-widest text-emerald-700">Frontend demo</p>
		<h1 class="text-3xl font-bold tracking-tight sm:text-4xl">Reduction Railroad</h1>
		<p class="mt-3 max-w-2xl text-slate-600">A starting point for learning computational reductions. Explore the sample workspace below.</p>
	</header>
	<div class="grid overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm md:grid-cols-2">
		<section aria-labelledby="problem-heading" class="border-b border-slate-200 p-6 md:border-r md:border-b-0">
			<p class="text-xs font-semibold uppercase tracking-wider text-slate-500">Sample problem</p>
			<h2 id="problem-heading" class="mt-2 text-xl font-semibold">Hello, Railroad!</h2>
			<p class="mt-4 text-slate-600">Write a C++ program that prints the greeting below. Edit the starter code in the adjacent editor.</p>
			<h3 class="mt-6 text-sm font-semibold">Expected output</h3>
			<pre class="mt-2 overflow-auto rounded-lg bg-slate-100 p-4 text-sm">Hello, Railroad!</pre>
			<p class="mt-6 text-sm text-slate-500">This is an editor demo. Code is not saved, compiled, or submitted.</p>
		</section>
		<section aria-labelledby="editor-heading" class="min-w-0">
			<div class="flex items-center justify-between border-b border-slate-200 px-5 py-3">
				<h2 id="editor-heading" class="text-sm font-semibold">main.cpp</h2>
				<span class="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">C++ · CodeMirror</span>
			</div>
			<CodeEditor />
		</section>
	</div>
	<footer class="mt-6 text-sm text-slate-500">
		SvelteKit + Svelte · Tailwind CSS · CodeMirror (C++) · Svelte Flow installed for future graph work
	</footer>
</main>
