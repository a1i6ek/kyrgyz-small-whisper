"""Gradio demo for UlutSoftLLC/whisper-small-kyrgyz (from the model card).

Run: python -m backend.gradio_app
"""
import gradio as gr

from backend.asr import get_pipeline, transcribe_file


def transcribe(audio_path):
    return transcribe_file(audio_path) if audio_path else ""


iface = gr.Interface(
    fn=transcribe,
    inputs=gr.Audio(sources=["microphone", "upload"], type="filepath"),
    outputs="text",
    title="Whisper Small Kyrgyz",
    description="Realtime demo for Kyrgyz speech recognition using a fine-tuned Whisper small model.",
)

if __name__ == "__main__":
    get_pipeline()
    iface.launch()
