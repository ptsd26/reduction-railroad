<script>
	import { onMount } from 'svelte';
	import { basicSetup, EditorView } from 'codemirror';
	import { cpp } from '@codemirror/lang-cpp';

	/** @type {HTMLDivElement} */
	let container;
	let editor;

	export function getCode() {
		return editor.state.doc.toString();
	}

	onMount(() => {
		editor = new EditorView({
			parent: container,
			doc: '#include <iostream>\n\nint main() {\n    std::cout << "Hello, Railroad!\\n";\n    return 0;\n}\n',
			extensions: [
				basicSetup,
				cpp(),
				EditorView.contentAttributes.of({ 'aria-label': 'C++ source code' }),
				EditorView.theme({
					'&': { minHeight: '280px', fontSize: '14px' },
					'.cm-scroller': { overflow: 'auto' }
				})
			]
		});
		return () => editor.destroy();
	});
</script>

<div class="min-w-0 overflow-hidden" bind:this={container}></div>
