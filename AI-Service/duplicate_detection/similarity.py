from sentence_transformers import SentenceTransformer, util

MODEL_NAME = "all-MiniLM-L6-v2"

_model = None

def load_model():
    global _model
    if _model is None:
        print(f"Loading Sentence Transformer model '{MODEL_NAME}'...")
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def get_embedding(text: str):
    model = load_model()
    return model.encode(text, convert_to_tensor=True)

def compute_similarity(text_a: str, text_b: str) -> float:
    model = load_model()
    emb_a = model.encode(text_a, convert_to_tensor=True)
    emb_b = model.encode(text_b, convert_to_tensor=True)
    score = util.cos_sim(emb_a, emb_b)
    return float(score[0][0])
