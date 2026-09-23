import pandas as pd
import numpy as np
import random

# Configuration
NUM_ROWS = 600
TRANSPORT_TYPES = ["Metro", "Bus", "Local Train"]
LOCATIONS = ["Andheri", "Dadar", "Borivali", "Kurla", "Virar", "Churchgate", "Ghatkopar", "Thane"]
SEVERITY_INDICATORS = ["safety", "comfort", "cleanliness", "delay", "staff_behavior"]
# Desired probabilities for each severity to help hit target priority distribution
# safety, comfort, cleanliness, delay, staff_behavior
SEVERITY_WEIGHTS = [0.15, 0.35, 0.15, 0.20, 0.15]  # sum to 1.0

# Priority categories
PRIORITY_CATEGORIES = ["Low", "Medium", "High", "Critical"]

def generate_complaint_text(transport, location, severity):
    """Generate a complaint text that matches the given severity indicator.
    Multiple templates per severity are provided.
    """
    if severity == "safety":
        templates = [
            f"Smoke was seen coming from the {transport.lower()} at {location}.",
            f"A passenger fell due to a broken step at {location} station.",
            f"Exposed live wire spotted near the {transport.lower()} platform at {location}.",
            f"Dangerous crowding caused a stampede near the {transport.lower()} at {location}.",
            f"A commuter was injured after falling near the {transport.lower()} at {location}.",
            f"Fire alarm triggered due to sparks near the {transport.lower()} platform at {location}.",
            f"Electrical short caused sparks and smoke near the {transport.lower()} at {location}.",
        ]
    elif severity == "staff_behavior":
        templates = [
            f"Staff at {location} was rude and unhelpful to commuters.",
            f"Ticket checker at {location} behaved inappropriately.",
            f"Security guard at {location} used excessive force.",
            f"Customer service at the {transport.lower()} station in {location} ignored complaints.",
        ]
    elif severity == "delay":
        templates = [
            f"The {transport.lower()} at {location} is frequently delayed beyond schedule.",
            f"Unexpected long delay of the {transport.lower()} caused commuters to miss connections at {location}.",
            f"Morning rush hour saw the {transport.lower()} stuck for over an hour at {location}.",
            f"The {transport.lower()} service at {location} has become unreliable with constant delays.",
        ]
    elif severity == "comfort":
        templates = [
            f"Overcrowding on the {transport.lower()} near {location} makes commuting difficult.",
            f"AC not working on the {transport.lower()} near {location} makes the ride uncomfortable.",
            f"Seats on the {transport.lower()} at {location} are often broken or missing.",
            f"Excessive heat and lack of ventilation on the {transport.lower()} at {location}.",
        ]
    elif severity == "cleanliness":
        templates = [
            f"The {transport.lower()} platform at {location} is littered and unclean.",
            f"Trash bins overflowed on the {transport.lower()} at {location}.",
            f"The carriage of the {transport.lower()} in {location} has foul odor and dirty floors.",
            f"Graffiti and spilled liquids on the {transport.lower()} platform at {location}.",
        ]
    else:
        templates = ["Generic complaint."]
    return random.choice(templates)

def assign_priority(severity, dup_score, prev_complaints):
    """Determine priority based on severity indicator and secondary modifiers.
    Returns one of the PRIORITY_CATEGORIES.
    """
    # Base priority mapping
    if severity == "safety":
        priority = "High"
        # Escalate to Critical only for very high duplicate score or many prior complaints
        if dup_score > 0.9 or prev_complaints > 15:
            priority = "Critical"
    elif severity == "staff_behavior":
        priority = "Medium"
        if dup_score > 0.8:
            priority = "High"
    elif severity == "delay":
        priority = "Medium"
        if dup_score > 0.8 or prev_complaints > 15:
            priority = "High"
    elif severity == "comfort":
        priority = "Low"
        if dup_score > 0.8:
            priority = "Medium"
    elif severity == "cleanliness":
        priority = "Low"
        if prev_complaints > 15:
            priority = "Medium"
    else:
        priority = "Low"
    return priority

def add_noise(priority):
    """Flip the priority with a small probability (≈12%)."""
    if random.random() < 0.12:
        other = [p for p in PRIORITY_CATEGORIES if p != priority]
        return random.choice(other)
    return priority

def main():
    data = []
    for _ in range(NUM_ROWS):
        transport = random.choice(TRANSPORT_TYPES)
        location = random.choice(LOCATIONS)
        severity = random.choice(SEVERITY_INDICATORS)
        complaint_text = generate_complaint_text(transport, location, severity)
        duplicate_score = round(random.uniform(0.0, 1.0), 3)
        previous_complaints = random.randint(0, 20)
        priority = add_noise(assign_priority(severity, duplicate_score, previous_complaints))
        row = {
            "complaint_text": complaint_text,
            "transport_type": transport,
            "location": location,
            "duplicate_score": duplicate_score,
            "previous_complaints": previous_complaints,
            "severity_indicator": severity,
            "priority": priority,
        }
        data.append(row)
    df = pd.DataFrame(data)
    # Save to CSV (overwrite existing file)
    csv_path = "datasets/priority_dataset.csv"
    df.to_csv(csv_path, index=False)

    # Print summary information
    print(f"Row count: {len(df)}")
    print("Priority distribution (count and %):")
    dist = df["priority"].value_counts().sort_index()
    total = len(df)
    for cat in PRIORITY_CATEGORIES:
        cnt = dist.get(cat, 0)
        pct = cnt / total * 100
        print(f"{cat}: {cnt} ({pct:.2f}%)")
    print("\nFirst 15 rows:")
    print(df.head(15).to_string(index=False))

if __name__ == "__main__":
    main()
