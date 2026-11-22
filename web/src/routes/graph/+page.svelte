<script>
    import {
        SvelteFlow,
    } from '@xyflow/svelte';
    import '@xyflow/svelte/dist/style.css';
    
    let { data } = $props();

    let nodes = $derived(
        data.problems.slugs.map((slug, i) => ({
            id: slug,
            position: { x: 0, y: i * 120 },
            data: { label: slug },
        }))
    );
    
    let edges = $state.raw([]);

    let reduce_from = $state(null);
    let reduce_to = $state(null);
</script>

<svelte:head>
  <title>Reduction Railroad Graph</title>
</svelte:head>

<main>
    <div style:width="100vw" style:height="100vh">
        <SvelteFlow 
            bind:nodes bind:edges fitView colorMode="system"
            onnodeclick={({ node }) => {
                if (!reduce_from && node.id != reduce_to) reduce_from = node.id;
                else if (node.id != reduce_from) reduce_to = node.id;
            }}
            onpaneclick={() => (reduce_from = null, reduce_to = null)}
        >
        </SvelteFlow>
    </div>

    {#if reduce_from || reduce_to}
        <aside class="sidebar">
            <h2>Reduce {reduce_from}</h2>
            <h2>To {reduce_to}</h2>
            <button onclick={() => {}}>Reduce!</button>
            <button onclick={() => ( reduce_from = null )}>Clear from</button>
            <button onclick={() => ( reduce_to = null)}>Clear to</button>
        </aside>
    {/if}
</main>

<style>
    .sidebar {
        position: fixed;
        top: 0;
        left: 0;
        width: 320px;
        height: 100vh;
        background: white;
    }
</style>