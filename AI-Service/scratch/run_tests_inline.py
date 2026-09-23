import time, json, requests, sys

BASE_URL = "http://127.0.0.1:8000"

def print_resp(name, resp):
    print(f"--- {name} ---")
    print("Status code:", resp.status_code)
    try:
        data = resp.json()
        print("JSON body:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print("Could not parse JSON. Raw body:")
        print(resp.text)
    print()

# give server a moment to start
time.sleep(2)

# 1. speech-to-text (dummy file)
try:
    audio_path = "datasets/audio_samples/sample_english.mp3"
    with open(audio_path, "rb") as f:
        files = {"voiceFile": f}
        resp = requests.post(f"{BASE_URL}/ai/speech-to-text", files=files)
    print_resp("speech-to-text", resp)
except Exception as e:
    print("Error in speech-to-text:", e)
    sys.exit(1)

# 2. translate
try:
    resp = requests.post(f"{BASE_URL}/ai/translate", json={"text": "मेट्रो उशिरा आहे", "source": "mr"})
    print_resp("translate", resp)
except Exception as e:
    print("Error in translate:", e)
    sys.exit(1)

# 3. detect duplicate
try:
    resp = requests.post(f"{BASE_URL}/ai/detect-duplicate", json={"text": "The escalator near Andheri Metro entrance is broken.", "id": "TEST1"})
    print_resp("detect-duplicate", resp)
except Exception as e:
    print("Error in detect-duplicate:", e)
    sys.exit(1)

# 4. predict priority
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
    print_resp("predict-priority", resp)
except Exception as e:
    print("Error in predict-priority:", e)
    sys.exit(1)
