from speech_to_text.transcriber import transcribe_audio

if __name__ == "__main__":
    samples = [
        "datasets/audio_samples/sample_english.mp3",
        "datasets/audio_samples/sample_hindi.mp3",
        "datasets/audio_samples/sample_marathi.mp3",
    ]

    for path in samples:
        print(f"\n--- Transcribing: {path} ---")
        output = transcribe_audio(path)
        print("Detected language:", output["language"])
        print("Transcribed text :", output["text"])
