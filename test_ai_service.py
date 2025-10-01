import requests
import json

# Test AI service
url = "http://localhost:8000/generate-quiz"
data = {
    "userPrompt": "Toi muon di Da Nang ngay 2025-10-10 2 dem, co phong gym",
    "currentParams": {}
}

try:
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    print("Response:")
    result = response.json()
    print("Quiz completed:", result.get('quiz_completed'))
    print("Key to collect:", result.get('key_to_collect'))
    print("Missing quiz:", result.get('missing_quiz'))
    print("Final params:", result.get('final_params'))
except Exception as e:
    print("Error:", e)
