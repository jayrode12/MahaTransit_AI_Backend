from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

MODEL_NAME = "facebook/nllb-200-distilled-600M"

_model = None
_tokenizer = None

# NLLB uses specific language codes, not simple 2-letter codes
LANG_CODE_MAP = {
    "hi": "hin_Deva",   # Hindi
    "mr": "mar_Deva",   # Marathi
    "en": "eng_Latn",   # English
}

def load_model():
    global _model, _tokenizer
    if _model is None:
        print(f"Loading NLLB model '{MODEL_NAME}'... (only happens once)")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return _model, _tokenizer

def translate_to_english(text: str, source_lang: str) -> str:
    """
    source_lang: 'hi', 'mr', or 'en'
    Returns the English translation. If source_lang is already 'en',
    returns the text unchanged (no need to translate English to English).
    """
    if source_lang == "en":
        return text

    if source_lang not in LANG_CODE_MAP:
        raise ValueError(f"Unsupported source language: {source_lang}")

    model, tokenizer = load_model()
    src_code = LANG_CODE_MAP[source_lang]
    tgt_code = LANG_CODE_MAP["en"]

    tokenizer.src_lang = src_code
    inputs = tokenizer(text, return_tensors="pt")

    forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_code)
    generated_tokens = model.generate(
        **inputs,
        forced_bos_token_id=forced_bos_token_id,
        max_length=200
    )

    result = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    return result[0]
