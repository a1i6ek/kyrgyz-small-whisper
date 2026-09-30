"""Shared Kyrgyz speech recognition model (UlutSoftLLC/whisper-small-kyrgyz)."""
import threading
from functools import lru_cache

import librosa
import numpy as np
import torch
from transformers import pipeline

MODEL_ID = "UlutSoftLLC/whisper-small-kyrgyz"
SAMPLE_RATE = 16000

DEVICE = "mps" if torch.backends.mps.is_available() else ("cuda:0" if torch.cuda.is_available() else "cpu")

# The pipeline isn't thread-safe; serialize inference.
_lock = threading.Lock()


@lru_cache(maxsize=1)
def get_pipeline():
    return pipeline("automatic-speech-recognition", model=MODEL_ID, device=DEVICE, chunk_length_s=30)


def transcribe_array(audio: np.ndarray, sr: int) -> str:
    """Transcribe mono float audio at any sample rate."""
    if sr != SAMPLE_RATE:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=SAMPLE_RATE)
    if audio.size == 0 or np.abs(audio).max() < 1e-4:
        return ""
    # The model was fine-tuned without a language token (Whisper has no Kyrgyz one),
    # so only the task is set.
    with _lock:
        result = get_pipeline()(
            {"raw": audio, "sampling_rate": SAMPLE_RATE},
            generate_kwargs={"task": "transcribe"},
        )
    return result["text"].strip()


def transcribe_file(path: str) -> str:
    # librosa loads wav/flac without ffmpeg; Whisper expects 16 kHz mono.
    audio, sr = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    return transcribe_array(audio, sr)
