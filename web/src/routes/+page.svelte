<script lang="ts">
	import { onDestroy, tick } from 'svelte';
	import { formatDuration, prepareAudio } from '$lib/audio';
	import VoiceMessage from '$lib/VoiceMessage.svelte';

	type Message =
		| { id: number; from: 'user'; time: Date; url: string; duration: number; peaks: number[] }
		| {
				id: number;
				from: 'bot';
				time: Date;
				status: 'pending' | 'done' | 'error';
				text: string;
		  };

	let messages: Message[] = $state([
		{
			id: 0,
			from: 'bot',
			time: new Date(),
			status: 'done',
			text: 'Саламатсызбы! Send me a voice message in Kyrgyz and I will reply with the transcription.'
		}
	]);
	let nextId = 1;

	let recorder: MediaRecorder | null = null;
	let chunks: Blob[] = [];
	let cancelled = false;
	let recording = $state(false);
	let elapsed = $state(0);
	let timer: ReturnType<typeof setInterval> | undefined;
	let micError = $state('');

	let scroller: HTMLElement | undefined = $state();
	let fileInput: HTMLInputElement | undefined = $state();

	async function scrollToBottom() {
		await tick();
		scroller?.scrollTo({ top: scroller.scrollHeight, behavior: 'smooth' });
	}

	async function startRecording() {
		micError = '';
		let stream: MediaStream;
		try {
			stream = await navigator.mediaDevices.getUserMedia({ audio: true });
		} catch {
			micError = 'Microphone access was denied.';
			return;
		}

		chunks = [];
		cancelled = false;
		recorder = new MediaRecorder(stream);
		recorder.ondataavailable = (e) => e.data.size && chunks.push(e.data);
		recorder.onstop = () => {
			stream.getTracks().forEach((t) => t.stop());
			clearInterval(timer);
			recording = false;
			if (!cancelled && chunks.length) {
				void send(new Blob(chunks, { type: recorder?.mimeType || 'audio/webm' }));
			}
		};
		recorder.start();
		recording = true;
		elapsed = 0;
		const startedAt = Date.now();
		timer = setInterval(() => (elapsed = (Date.now() - startedAt) / 1000), 200);
	}

	function stopRecording(cancel = false) {
		cancelled = cancel;
		if (recorder?.state === 'recording') recorder.stop();
	}

	function onFilePicked(event: Event) {
		const input = event.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		input.value = '';
		if (file) void send(file);
	}

	async function send(blob: Blob) {
		let prepared;
		try {
			prepared = await prepareAudio(blob);
		} catch {
			micError = 'Could not decode that audio.';
			return;
		}

		messages.push({
			id: nextId++,
			from: 'user',
			time: new Date(),
			url: URL.createObjectURL(blob),
			duration: prepared.duration,
			peaks: prepared.peaks
		});
		const replyId = nextId++;
		messages.push({ id: replyId, from: 'bot', time: new Date(), status: 'pending', text: '' });
		void scrollToBottom();

		// Update through the proxied array item so the change is reactive.
		const reply = messages.find((m) => m.id === replyId) as Extract<Message, { from: 'bot' }>;
		try {
			const body = new FormData();
			body.append('audio', prepared.wav, 'voice.wav');
			const res = await fetch('/api/transcribe', { method: 'POST', body });
			if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail ?? res.statusText);
			const { text } = (await res.json()) as { text: string };
			reply.text = text || '(no speech detected)';
			reply.status = 'done';
		} catch (e) {
			reply.text = `Error: ${e instanceof Error ? e.message : 'request failed'}`;
			reply.status = 'error';
		}
		reply.time = new Date();
		void scrollToBottom();
	}

	function formatTime(d: Date) {
		return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	}

	onDestroy(() => {
		stopRecording(true);
		for (const m of messages) if (m.from === 'user') URL.revokeObjectURL(m.url);
	});
</script>

<svelte:head>
	<title>Kyrgyz ASR Chat</title>
</svelte:head>

<div class="app">
	<header>
		<div class="avatar">KG</div>
		<div>
			<div class="name">Kyrgyz ASR Bot</div>
			<div class="status">
				{messages.some((m) => m.from === 'bot' && m.status === 'pending') ? 'typing…' : 'bot'}
			</div>
		</div>
	</header>

	<main bind:this={scroller}>
		<div class="messages">
			{#each messages as message (message.id)}
				<div class="row" class:out={message.from === 'user'}>
					<div class="bubble" class:out={message.from === 'user'}>
						{#if message.from === 'user'}
							<VoiceMessage src={message.url} duration={message.duration} peaks={message.peaks} />
						{:else if message.status === 'pending'}
							<div class="typing" aria-label="Transcribing"><span></span><span></span><span></span></div>
						{:else}
							<p class="text" class:error={message.status === 'error'}>{message.text}</p>
						{/if}
						{#if message.from === 'user' || message.status !== 'pending'}
							<span class="meta">
								{formatTime(message.time)}
								{#if message.from === 'user'}
									<svg viewBox="0 0 18 12" width="16" height="11" aria-hidden="true"
										><path
											d="M1 6.5l3.5 3.5L11 3.5M7 10l6.5-6.5"
											fill="none"
											stroke="currentColor"
											stroke-width="1.6"
											stroke-linecap="round"
											stroke-linejoin="round"
										/></svg
									>
								{/if}
							</span>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	</main>

	<footer>
		{#if micError}
			<div class="mic-error">{micError}</div>
		{/if}
		<div class="composer">
			{#if recording}
				<div class="recording">
					<span class="dot"></span>
					<span>{formatDuration(elapsed)}</span>
				</div>
				<button class="cancel" onclick={() => stopRecording(true)}>Cancel</button>
				<button class="round send" onclick={() => stopRecording()} aria-label="Send voice message">
					<svg viewBox="0 0 24 24" width="22" height="22"
						><path d="M3 20.5 21 12 3 3.5 3 10l12 2-12 2z" fill="currentColor" /></svg
					>
				</button>
			{:else}
				<button class="icon" onclick={() => fileInput?.click()} aria-label="Attach audio file">
					<svg viewBox="0 0 24 24" width="24" height="24"
						><path
							d="M16.5 6.5v10a4.5 4.5 0 0 1-9 0V5a3 3 0 0 1 6 0v10.5a1.5 1.5 0 0 1-3 0V6.5"
							fill="none"
							stroke="currentColor"
							stroke-width="1.7"
							stroke-linecap="round"
						/></svg
					>
				</button>
				<input
					bind:this={fileInput}
					type="file"
					accept="audio/*"
					hidden
					onchange={onFilePicked}
				/>
				<div class="hint">Tap the mic to record a voice message</div>
				<button class="round" onclick={startRecording} aria-label="Record voice message">
					<svg viewBox="0 0 24 24" width="22" height="22"
						><path
							d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11z"
							fill="currentColor"
						/></svg
					>
				</button>
			{/if}
		</div>
	</footer>
</div>

<style>
	:global(:root) {
		--bg: #8fb48a;
		--pattern: rgba(255, 255, 255, 0.12);
		--panel: #ffffff;
		--bubble-in: #ffffff;
		--bubble-out: #e3fdd0;
		--text: #0f1419;
		--meta: #6a8a6a;
		--meta-in: #8b9aa6;
		--accent: #3390ec;
		--voice-accent: #4fae4e;
		--voice-on-accent: #ffffff;
		--voice-bar: #a9d3a0;
		--error: #d93a3a;
		--shadow: 0 1px 2px rgba(16, 35, 47, 0.15);
	}

	@media (prefers-color-scheme: dark) {
		:global(:root) {
			--bg: #0e1621;
			--pattern: rgba(255, 255, 255, 0.03);
			--panel: #17212b;
			--bubble-in: #182533;
			--bubble-out: #2b5278;
			--text: #f5f5f5;
			--meta: #7da8d3;
			--meta-in: #6d7f8f;
			--accent: #5eb5f7;
			--voice-accent: #5eb5f7;
			--voice-on-accent: #17212b;
			--voice-bar: #4c7197;
			--error: #ff6b6b;
			--shadow: none;
		}
	}

	:global(body) {
		margin: 0;
		font-family:
			-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
		color: var(--text);
		background: var(--bg);
	}

	.app {
		display: flex;
		flex-direction: column;
		height: 100dvh;
		background-color: var(--bg);
		background-image: radial-gradient(var(--pattern) 1.5px, transparent 1.5px);
		background-size: 22px 22px;
	}

	header {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 8px 16px;
		background: var(--panel);
		box-shadow: var(--shadow);
		z-index: 1;
	}

	.avatar {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		display: grid;
		place-items: center;
		font-weight: 600;
		color: #fff;
		background: linear-gradient(135deg, #72d5fd, #2a9ef1);
	}

	.name {
		font-weight: 600;
	}

	.status {
		font-size: 13px;
		color: var(--accent);
	}

	main {
		flex: 1;
		overflow-y: auto;
	}

	.messages {
		max-width: 720px;
		margin: 0 auto;
		padding: 16px 12px;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.row {
		display: flex;
	}

	.row.out {
		justify-content: flex-end;
	}

	.bubble {
		position: relative;
		max-width: min(480px, 82%);
		padding: 7px 10px 6px;
		border-radius: 14px 14px 14px 4px;
		background: var(--bubble-in);
		box-shadow: var(--shadow);
		display: flex;
		flex-wrap: wrap;
		align-items: flex-end;
		gap: 2px 10px;
	}

	.bubble.out {
		border-radius: 14px 14px 4px 14px;
		background: var(--bubble-out);
	}

	.text {
		margin: 0;
		white-space: pre-wrap;
		overflow-wrap: anywhere;
		line-height: 1.35;
	}

	.text.error {
		color: var(--error);
	}

	.meta {
		margin-left: auto;
		display: inline-flex;
		align-items: center;
		gap: 3px;
		font-size: 12px;
		color: var(--meta-in);
	}

	.bubble.out .meta {
		color: var(--meta);
	}

	.typing {
		display: flex;
		gap: 4px;
		padding: 6px 2px;
	}

	.typing span {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--meta-in);
		animation: blink 1.2s infinite ease-in-out;
	}

	.typing span:nth-child(2) {
		animation-delay: 0.2s;
	}

	.typing span:nth-child(3) {
		animation-delay: 0.4s;
	}

	@keyframes blink {
		0%,
		80%,
		100% {
			opacity: 0.3;
			transform: translateY(0);
		}
		40% {
			opacity: 1;
			transform: translateY(-3px);
		}
	}

	footer {
		padding: 8px 12px 12px;
	}

	.mic-error {
		max-width: 720px;
		margin: 0 auto 6px;
		font-size: 13px;
		color: var(--error);
		text-align: center;
	}

	.composer {
		max-width: 720px;
		margin: 0 auto;
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 6px 6px 6px 10px;
		border-radius: 24px;
		background: var(--panel);
		box-shadow: var(--shadow);
	}

	.hint {
		flex: 1;
		color: var(--meta-in);
		font-size: 15px;
	}

	.icon {
		border: none;
		background: none;
		color: var(--meta-in);
		cursor: pointer;
		display: grid;
		place-items: center;
		padding: 4px;
	}

	.round {
		flex: none;
		width: 44px;
		height: 44px;
		border-radius: 50%;
		border: none;
		display: grid;
		place-items: center;
		color: #fff;
		background: var(--accent);
		cursor: pointer;
	}

	.round.send {
		animation: pulse 1.4s infinite;
	}

	@keyframes pulse {
		0% {
			box-shadow: 0 0 0 0 color-mix(in srgb, var(--accent) 50%, transparent);
		}
		100% {
			box-shadow: 0 0 0 12px transparent;
		}
	}

	.recording {
		flex: 1;
		display: flex;
		align-items: center;
		gap: 8px;
		font-variant-numeric: tabular-nums;
	}

	.dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: var(--error);
		animation: blink-dot 1s infinite;
	}

	@keyframes blink-dot {
		50% {
			opacity: 0.2;
		}
	}

	.cancel {
		border: none;
		background: none;
		color: var(--accent);
		font-size: 15px;
		cursor: pointer;
	}
</style>
