<script lang="ts">
  import CodeEditor from "#lib/CodeEditor.svelte";
  import { Button } from "#lib/components/ui/button/index.ts";
  import type { SubmitResponse } from "./api/submissions/+server";
  import type { GetSubmissionResponse } from "./api/submissions/[submissionId]/+server";

  let editorRef: CodeEditor;
  let submissionStatus = $state("");

  async function submitCode() {
    console.log("Pressed submit button");
    let from = "sat";
    let to = "clique";
    let sourceCode = editorRef.getCode();

    // Post the submission
    const res = await fetch("/api/submissions", {
      method: "POST",
      body: JSON.stringify({
        fromProblem: from,
        toProblem: to,
        source: sourceCode,
      }),
    });

    // Check that the POST was ok
    if (!res.ok) {
      const { error } = await res.json();
      submissionStatus = `Error ${res.status}: ${error}`;
      return;
    }

    const submitResponse: SubmitResponse = await res.json();
    submissionStatus = `Submission #${submitResponse.id}: queued`;

    // Poll submission result until it has a verdict
    // TODO: Replace this with a connection to an SSE stream (connecting to /api/submissions/[id]/events)
    let submission: GetSubmissionResponse;
    do {
      // Wait a little bit
      await new Promise((r) => setTimeout(r, 1000));

      // Poll the submission details
      const details = await fetch(`/api/submissions/${submitResponse.id}`);
      if (!details.ok) {
        const { error } = await details.json();
        submissionStatus = `Error ${details.status}: ${error}`;
        return;
      }

      // Update the displayed status
      submission = await details.json();
      submissionStatus = `Submission #${submitResponse.id}: ${submission.status}`;
    } while (submission.status !== "done");

    // Once judging is done, display the verdict instead of "status: done"
    submissionStatus = `Submission #${submitResponse.id}: ${submission.verdict}`;
  }
</script>

<svelte:head>
  <title>Reduction Railroad | Frontend demo</title>
  <meta
    name="description"
    content="A minimal Reduction Railroad frontend demo with a C++ editor."
  />
</svelte:head>

<main class="mx-auto max-w-6xl px-4 py-10 sm:px-8">
  <header class="mb-8">
    <p
      class="mb-2 text-sm font-semibold uppercase tracking-widest text-emerald-700"
    >
      Frontend demo
    </p>
    <h1 class="text-3xl font-bold tracking-tight sm:text-4xl">
      Reduction Railroad
    </h1>
    <p class="mt-3 max-w-2xl text-slate-600">
      A starting point for learning computational reductions. Explore the sample
      workspace below.
    </p>
  </header>
  <div
    class="grid overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm md:grid-cols-2"
  >
    <section
      aria-labelledby="problem-heading"
      class="border-b border-slate-200 p-6 md:border-r md:border-b-0"
    >
      <p class="text-xs font-semibold uppercase tracking-wider text-slate-500">
        Sample problem
      </p>
      <h2 id="problem-heading" class="mt-2 text-xl font-semibold">
        Hello, World!
      </h2>
      <p class="mt-4 text-slate-600">
        Write a C++ program that prints the greeting below. Edit the starter
        code in the adjacent editor.
      </p>
      <h3 class="mt-6 text-sm font-semibold">Expected output (case insensitive)</h3>
      <pre
        class="mt-2 overflow-auto rounded-lg bg-slate-100 p-4 text-sm">Hello, World!</pre>
    </section>
    <section aria-labelledby="editor-heading" class="min-w-0">
      <div
        class="flex items-center justify-between border-b border-slate-200 px-5 py-3"
      >
        <h2 id="editor-heading" class="text-sm font-semibold">main.cpp</h2>
        <span class="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600"
          >C++ · CodeMirror</span
        >
      </div>
      <CodeEditor bind:this={editorRef} />
      <Button id="submit-button" class="flex px-5" onclick={submitCode}>
        Submit
      </Button>
      {#if submissionStatus}
        <pre
          class="m-5 overflow-auto rounded-lg bg-slate-100 p-4 text-sm">{submissionStatus}</pre>
      {/if}
    </section>
  </div>

  <footer class="mt-6 text-sm text-slate-500">
    SvelteKit + Svelte · Tailwind CSS · CodeMirror (C++) · Svelte Flow installed
    for future graph work
  </footer>
</main>
