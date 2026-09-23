from itertools import combinations
from datasets.sample_complaints import SAMPLE_COMPLAINTS
from duplicate_detection.similarity import compute_similarity

if __name__ == "__main__":
    results = []
    for a, b in combinations(SAMPLE_COMPLAINTS, 2):
        score = compute_similarity(a["text"], b["text"])
        results.append((a["id"], b["id"], a["text"], b["text"], score))

    # Sort highest similarity first, so true duplicates should float to the top
    results.sort(key=lambda x: x[4], reverse=True)

    print(f"\n{'Pair':<10} {'Score':<8} Texts")
    print("-" * 100)
    for id_a, id_b, text_a, text_b, score in results:
        print(f"{id_a}-{id_b:<6} {score:.4f}   [{text_a}]  <->  [{text_b}]")
