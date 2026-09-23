from duplicate_detection.similarity import load_model
from duplicate_detection.duplicate_checker import check_duplicate
from datasets.sample_complaints import SAMPLE_COMPLAINTS

if __name__ == "__main__":
    model = load_model()

    # Simulate a database: precompute embeddings and add a duplicate_group_id field
    existing = []
    for c in SAMPLE_COMPLAINTS:
        existing.append({
            "id": c["id"],
            "text": c["text"],
            "embedding": model.encode(c["text"], convert_to_tensor=True),
            "duplicate_group_id": None
        })

    # New incoming complaints to test - some are duplicates, one is genuinely new
    new_complaints = [
        {"id": "NEW1", "text": "The escalator near Andheri Metro entrance is broken."},
        {"id": "NEW2", "text": "Local train ticket window at Dadar is closed / machine faulty."},
        {"id": "NEW3", "text": "Pigeon droppings all over the platform benches at Kurla station."},
    ]

    for new_c in new_complaints:
        result = check_duplicate(new_c["text"], new_c["id"], existing)
        print(f"\n--- New complaint {new_c['id']}: \"{new_c['text']}\" ---")
        print("Is duplicate?      :", result["isDuplicate"])
        print("Duplicate of       :", result["duplicateOf"])
        print("Similarity score   :", result["score"])
        print("Assigned group ID  :", result["assigned_group_id"])

        # Simulate saving the new complaint into "existing" for future checks
        existing.append({
            "id": new_c["id"],
            "text": new_c["text"],
            "embedding": model.encode(new_c["text"], convert_to_tensor=True),
            "duplicate_group_id": result["assigned_group_id"]
        })
