import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import xgboost as xgb
import joblib

# Paths
DATA_PATH = "datasets/priority_dataset.csv"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

print(f"Loading data from {DATA_PATH} ...")
# 1. Load dataset
df = pd.read_csv(DATA_PATH)

# Ensure expected columns exist
expected_cols = {"complaint_text", "transport_type", "location", "duplicate_score", "previous_complaints", "priority"}
missing = expected_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing columns in CSV: {missing}")

# 2. Encode complaint_text using SentenceTransformer (same model as Phase 3)
print("Loading SentenceTransformer model ...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Encoding complaint texts ...")
text_embeddings = model.encode(df["complaint_text"].tolist(), show_progress_bar=True)

# 3. One‑hot encode categorical columns
categorical_cols = ["transport_type", "location", "severity_indicator"]
print(f"One-hot encoding categorical columns: {categorical_cols} ...")
encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
cat_features = encoder.fit_transform(df[categorical_cols])

# 4. Assemble final feature matrix
numeric_features = df[["duplicate_score", "previous_complaints"]].values
X = np.hstack([text_embeddings, cat_features, numeric_features])

# 5. Encode target labels
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(df["priority"])
print("Label mapping:")
for class_idx, class_label in enumerate(label_encoder.classes_):
    print(f"  {class_label} = {class_idx}")

# 6. Train‑test split (stratified)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 7. Train XGBoost classifier
print("Training XGBoost classifier ...")
clf = xgb.XGBClassifier(
    objective="multi:softprob",
    num_class=len(label_encoder.classes_),
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    eval_metric="mlogloss",
    use_label_encoder=False,
    verbosity=0,
)
clf.fit(X_train, y_train)

# 8. Evaluation on test set
print("Evaluating model ...")
y_pred = clf.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"\nOverall accuracy: {acc:.4f}\n")
print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# Confusion matrix as a readable table
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix (rows = true, cols = predicted):")
# Header row
header = "".join([f"{lbl:>10}" for lbl in label_encoder.classes_])
print(f"{'':>10}{header}")
for i, row in enumerate(cm):
    row_str = "".join([f"{val:>10}" for val in row])
    print(f"{label_encoder.classes_[i]:>10}{row_str}")

# 9. Save artefacts
model_path = os.path.join(MODEL_DIR, "priority_model.pkl")
encoder_path = os.path.join(MODEL_DIR, "priority_encoder.pkl")
label_encoder_path = os.path.join(MODEL_DIR, "priority_label_encoder.pkl")
print("\nSaving model and encoders ...")
joblib.dump(clf, model_path)
joblib.dump(encoder, encoder_path)
joblib.dump(label_encoder, label_encoder_path)
print(f"Model saved to {model_path}")
print(f"Encoder saved to {encoder_path}")
print(f"LabelEncoder saved to {label_encoder_path}")
