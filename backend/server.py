"""FastAPI backend: receives a voice message and replies with its Kyrgyz transcription.

Run: make backend  (or: .venv/bin/uvicorn backend.server:app --port 8010)
"""
import io

import soundfile as sf
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from backend.asr import DEVICE, MODEL_ID, get_pipeline, transcribe_array

get_pipeline()  # load the model at startup, not on the first request

app = FastAPI(title="Kyrgyz ASR chat")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5180", "http://127.0.0.1:5180"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def transcribe_bytes(data: bytes) -> str:
    # The web UI sends 16 kHz mono WAV, but accept anything soundfile can read.
    audio, sr = sf.read(io.BytesIO(data), dtype="float32", always_2d=True)
    return transcribe_array(audio.mean(axis=1), sr)


@app.get("/api/health")
def health():
    return {"status": "ok", "model": MODEL_ID, "device": DEVICE}


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    data = await audio.read()
    if not data:
        raise HTTPException(400, "Empty audio")
    try:
        text = await run_in_threadpool(transcribe_bytes, data)
    except sf.LibsndfileError as e:
        raise HTTPException(415, f"Unsupported audio format: {e}")
    return {"text": text}
