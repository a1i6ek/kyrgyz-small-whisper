const TARGET_RATE = 16000;

export type PreparedAudio = {
	/** 16 kHz mono 16-bit PCM WAV, ready for the backend. */
	wav: Blob;
	/** Duration in seconds. */
	duration: number;
	/** Normalized (0..1) amplitude bars for the waveform. */
	peaks: number[];
};

/**
 * Decode any browser-supported audio (webm/opus from MediaRecorder, mp3, m4a, …)
 * and resample it to 16 kHz mono WAV, so the backend doesn't need ffmpeg.
 */
export async function prepareAudio(blob: Blob, bars = 36): Promise<PreparedAudio> {
	const ctx = new AudioContext();
	let decoded: AudioBuffer;
	try {
		decoded = await ctx.decodeAudioData(await blob.arrayBuffer());
	} finally {
		void ctx.close();
	}

	const length = Math.max(1, Math.ceil(decoded.duration * TARGET_RATE));
	// A 1-channel offline context downmixes stereo input automatically.
	const offline = new OfflineAudioContext(1, length, TARGET_RATE);
	const source = offline.createBufferSource();
	source.buffer = decoded;
	source.connect(offline.destination);
	source.start();
	const samples = (await offline.startRendering()).getChannelData(0);

	return {
		wav: encodeWav(samples, TARGET_RATE),
		duration: decoded.duration,
		peaks: computePeaks(samples, bars)
	};
}

function encodeWav(samples: Float32Array, sampleRate: number): Blob {
	const buffer = new ArrayBuffer(44 + samples.length * 2);
	const view = new DataView(buffer);
	const writeString = (offset: number, s: string) => {
		for (let i = 0; i < s.length; i++) view.setUint8(offset + i, s.charCodeAt(i));
	};

	writeString(0, 'RIFF');
	view.setUint32(4, 36 + samples.length * 2, true);
	writeString(8, 'WAVE');
	writeString(12, 'fmt ');
	view.setUint32(16, 16, true); // PCM chunk size
	view.setUint16(20, 1, true); // PCM format
	view.setUint16(22, 1, true); // mono
	view.setUint32(24, sampleRate, true);
	view.setUint32(28, sampleRate * 2, true); // byte rate
	view.setUint16(32, 2, true); // block align
	view.setUint16(34, 16, true); // bits per sample
	writeString(36, 'data');
	view.setUint32(40, samples.length * 2, true);

	for (let i = 0; i < samples.length; i++) {
		const s = Math.max(-1, Math.min(1, samples[i]));
		view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
	}
	return new Blob([buffer], { type: 'audio/wav' });
}

function computePeaks(samples: Float32Array, bars: number): number[] {
	const size = Math.max(1, Math.floor(samples.length / bars));
	const peaks: number[] = [];
	for (let b = 0; b < bars; b++) {
		let max = 0;
		for (let i = b * size; i < Math.min((b + 1) * size, samples.length); i++) {
			max = Math.max(max, Math.abs(samples[i]));
		}
		peaks.push(max);
	}
	const top = Math.max(...peaks, 1e-3);
	return peaks.map((p) => Math.max(0.08, p / top));
}

export function formatDuration(seconds: number): string {
	const s = Math.max(0, Math.round(seconds));
	return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}
