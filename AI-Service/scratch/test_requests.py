import requests, json, traceback, os

BASE_URL = "http://127.0.0.1:8000"

def print_response(name, resp):
    print(f"--- {name} ---")
    print("Status code:", resp.status_code)
    try:
        data = resp.json()
        print("JSON body:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print("Failed to parse JSON. Raw response:")
        print(resp.text)

def main():
    # 1. Speech-to-Text
    try:
        audio_path = os.path.join("datasets", "audio_samples", "sample_english.mp3")
        with open(audio_path, "rb") as f:
            files = {"voiceFile": f}
            resp = requests.post(f"{BASE_URL}/ai/speech-to-text", files=files)
        print_response("speech-to-text", resp)
    except Exception:
        print("Error in speech-to-text request:")
        traceback.print_exc()

    # 2. Translate
    try:
        resp = requests.post(
            f"{BASE_URL}/ai/translate",
            json={"text": "मेट्रो उशिरा आहे", "source": "mr"},
        )
        print_response("translate", resp)
    except Exception:
        print("Error in translate request:")
        traceback.print_exc()

    # 3. Detect Duplicate
    try:
        resp = requests.post(
            f"{BASE_URL}/ai/detect-duplicate",
            json={"text": "The escalator near Andheri Metro entrance is broken.", "id": "TEST1"},
        )
        print_response("detect-duplicate", resp)
    except Exception:
        print("Error in detect-duplicate request:")
        traceback.print_exc()

    # 4. Predict Priority
    try:
        payload = {
            "text": "Smoke was seen coming from the local train at Borivali.",
            "transport_type": "Local Train",
            "location": "Borivali",
            "duplicate_score": 0.8,
            "previous_complaints": 5,
            "severity_indicator": "safety",
        }
        resp = requests.post(f"{BASE_URL}/ai/predict-priority", json=payload)
        print_response("predict-priority", resp)
    except Exception:
        print("Error in predict-priority request:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
