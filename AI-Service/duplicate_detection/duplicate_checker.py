from duplicate_detection.similarity import load_model
from sentence_transformers import util

SIMILARITY_THRESHOLD = 0.55

def check_duplicate(new_text: str, new_id: str, existing_complaints: list) -> dict:
    """
    existing_complaints: list of dicts, each with keys:
        'id', 'text', 'embedding' (precomputed), 'duplicate_group_id' (or None)
    
    Compares new_text against every complaint in existing_complaints,
    finds the best match, and decides if it's a duplicate.
    
    Returns a dict describing the result AND the duplicate_group_id 
    that should be assigned to the new complaint (None if unique).
    """
    model = load_model()
    new_embedding = model.encode(new_text, convert_to_tensor=True)

    best_match = None
    best_score = -1.0

    for complaint in existing_complaints:
        if complaint["id"] == new_id:
            continue  # never compare a complaint against itself

        score = float(util.cos_sim(new_embedding, complaint["embedding"])[0][0])
        if score > best_score:
            best_score = score
            best_match = complaint

    is_duplicate = best_score >= SIMILARITY_THRESHOLD

    if not is_duplicate:
        return {
            "isDuplicate": False,
            "duplicateOf": None,
            "score": round(best_score, 4) if best_match else None,
            "assigned_group_id": None
        }

    # It IS a duplicate. Figure out the group ID to assign.
    if best_match["duplicate_group_id"] is not None:
        # Best match already belongs to a group - join it
        assigned_group_id = best_match["duplicate_group_id"]
    else:
        # Best match has no group yet - create a new one for both
        assigned_group_id = f"GROUP-{best_match['id']}"
        best_match["duplicate_group_id"] = assigned_group_id  # backfill it

    return {
        "isDuplicate": True,
        "duplicateOf": best_match["id"],
        "score": round(best_score, 4),
        "assigned_group_id": assigned_group_id
    }
