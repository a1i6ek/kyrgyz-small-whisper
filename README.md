# Kyrgyz ASR Chat

Telegram-style chat: send a voice message, get the Kyrgyz transcription back.
Uses [UlutSoftLLC/whisper-small-kyrgyz](https://huggingface.co/UlutSoftLLC/whisper-small-kyrgyz)
with a FastAPI backend and a SvelteKit web UI.

## Structure

```
backend/
  asr.py          model loading + transcription (shared)
  server.py       FastAPI API: POST /api/transcribe, GET /api/health
  cli.py          command-line transcription
  gradio_app.py   original Gradio demo from the model card
web/              SvelteKit chat UI (proxies /api to the backend)
samples/          example audio files
```

## Quick start

Requires Python 3.11, [bun](https://bun.sh) (or `JS=npm`), macOS/Linux.

```bash
make install   # .venv + requirements.txt + web deps
make dev       # API on :8010, web UI on http://localhost:5180
```

Other targets: `make help`. Transcribe a file: `make transcribe FILE=samples/audio.wav`.

The first run downloads the model (~1 GB) from Hugging Face.
