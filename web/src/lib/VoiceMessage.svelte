<script lang="ts">
	import { formatDuration } from '$lib/audio';

	let { src, duration, peaks }: { src: string; duration: number; peaks: number[] } = $props();

	let audio: HTMLAudioElement | undefined = $state();
	let paused = $state(true);
	let currentTime = $state(0);

	const progress = $derived(duration > 0 ? currentTime / duration : 0);

	function toggle() {
		if (!audio) return;
		if (audio.paused) void audio.play();
		else audio.pause();
	}

	function seek(event: MouseEvent) {
		if (!audio) return;
		const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
		audio.currentTime = ((event.clientX - rect.left) / rect.width) * duration;
	}
</script>

<div class="voice">
	<button class="play" onclick={toggle} aria-label={paused ? 'Play' : 'Pause'}>
		{#if paused}
			<svg viewBox="0 0 24 24" width="22" height="22"><path d="M8 5v14l11-7z" fill="currentColor" /></svg>
		{:else}
			<svg viewBox="0 0 24 24" width="22" height="22"
				><path d="M7 5h4v14H7zM13 5h4v14h-4z" fill="currentColor" /></svg
			>
		{/if}
	</button>

	<div class="body">
		<button class="wave" onclick={seek} aria-label="Seek">
			{#each peaks as peak, i (i)}
				<span class="bar" class:played={i / peaks.length < progress} style:height="{peak * 100}%"
				></span>
			{/each}
		</button>
		<span class="time">{formatDuration(paused && currentTime === 0 ? duration : currentTime)}</span>
	</div>

	<audio
		bind:this={audio}
		{src}
		bind:paused
		bind:currentTime
		onended={() => (currentTime = 0)}
		preload="metadata"
	></audio>
</div>

<style>
	.voice {
		display: flex;
		align-items: center;
		gap: 10px;
		min-width: 220px;
	}

	.play {
		flex: none;
		width: 42px;
		height: 42px;
		border-radius: 50%;
		border: none;
		display: grid;
		place-items: center;
		background: var(--voice-accent);
		color: var(--voice-on-accent);
		cursor: pointer;
	}

	.body {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.wave {
		display: flex;
		align-items: center;
		gap: 2px;
		height: 24px;
		padding: 0;
		border: none;
		background: none;
		cursor: pointer;
	}

	.bar {
		flex: 1;
		min-width: 2px;
		border-radius: 2px;
		background: var(--voice-bar);
		transition: background 0.1s;
	}

	.bar.played {
		background: var(--voice-accent);
	}

	.time {
		font-size: 12px;
		color: var(--meta);
	}
</style>
