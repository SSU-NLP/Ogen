<script lang="ts">
	import favicon from "$lib/assets/favicon.svg";

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children()}

<style>
	:global(body) {
		font-family:
			"Inter",
			-apple-system,
			BlinkMacSystemFont,
			"Segoe UI",
			Roboto,
			sans-serif;
		margin: 0;
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
	}
</style>
