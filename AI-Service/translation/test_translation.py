from translation.translator import translate_to_english

if __name__ == "__main__":
    test_cases = [
        ("मेट्रो उशिरा आहे, मी खूप वेळ थांबलो आहे.", "mr"),
        ("मेट्रो लेट है, बहुत देर से खड़ा हूँ।", "hi"),
        ("The escalator at Andheri Metro is not working.", "en"),
    ]

    for text, lang in test_cases:
        print(f"\n--- Source ({lang}): {text} ---")
        translated = translate_to_english(text, lang)
        print("Translated (en):", translated)
