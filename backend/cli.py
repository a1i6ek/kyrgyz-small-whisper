"""Transcribe Kyrgyz audio files from the command line.

Usage: python -m backend.cli audio1.wav [audio2.flac ...]
"""
import sys

from backend.asr import transcribe_file


def main(paths):
    for path in paths:
        print(f"{path}: {transcribe_file(path)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
