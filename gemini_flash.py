import os, requests
from dotenv import load_dotenv

load_dotenv()
API_KEY  = os.getenv("EDENAI_API_KEY")
ENDPOINT = "https://api.edenai.run/v2/text/chat"
HEADERS  = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def chat(prompt):
    body = {
        "providers": "google/gemini-2.0-flash",
        "text": prompt,
        "chatbot_global_action": "You are a helpful assistant.",
        "previous_history": [],
        "temperature": 0.0,
        "max_tokens": 1000,
    }

    resp = requests.post(ENDPOINT, headers=HEADERS, json=body, timeout=90)
    data = resp.json()
    r = data.get("google/gemini-2.0-flash", {})

    if r.get("status") == "success":
        usage = r.get("usage", {})
        print(f"Answer : {r.get('generated_text', '').strip()}")
        print(f"Tokens : {usage.get('completion_tokens')} output / {usage.get('prompt_tokens')} input")
        print(f"Cost   : ${r.get('cost', 0):.6f}")
    else:
        print(f"ERROR: {r}")

if __name__ == "__main__":
    chat("What is the difference between supervised and unsupervised machine learning?")
