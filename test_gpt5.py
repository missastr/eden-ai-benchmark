import subprocess, time, json, requests

TASK = (
    "You are a Reddit user in r/movies. A post says: "
    "'What is the most underrated masterpiece of cinema that nobody talks about anymore?' "
    "Write a detailed, passionate Reddit comment recommending a film. "
    "Explain why it's underrated, what makes it special, and why people should watch it. "
    "Sound like a genuine film enthusiast, 4-5 sentences."
)

import os
from dotenv import load_dotenv
load_dotenv()
EDEN_API_KEY = os.getenv("EDENAI_API_KEY")

def run_openclaw(label):
    print(f"\n{'='*50}")
    print(f"Running: {label}")
    print(f"{'='*50}")
    start = time.time()
    result = subprocess.run(
        ["/home/eden/.npm-global/bin/openclaw", "agent", "--agent", "main",
         "--session-id", f"eval-{int(time.time())}", "-m", TASK, "--json"],
        capture_output=True, text=True, timeout=120
    )
    elapsed = round(time.time() - start, 1)
    data    = json.loads(result.stdout)
    text    = data.get("result", {}).get("payloads", [{}])[0].get("text", "").strip()
    print(f"⏱️  Response time: {elapsed}s")
    print(f"📝 Response:\n{text}")
    return text, elapsed

def get_cost(model_id, text):
    """Estimate tokens and cost via Eden AI usage endpoint."""
    headers = {"Authorization": f"Bearer {EDEN_API_KEY}"}
    payload = {
        "providers": model_id,
        "text": TASK,
        "max_tokens": 300
    }
    # Rough token estimate: 1 token ≈ 4 chars
    input_tokens  = len(TASK) // 4
    output_tokens = len(text) // 4
    return input_tokens, output_tokens

# ── GPT-5.1 run ──
text_gpt5, time_gpt5 = run_openclaw("GPT-5.1")
in_tok, out_tok = get_cost("openai/gpt-5.1", text_gpt5)

# GPT-5.1 pricing: ~$2.00/1M input, ~$8.00/1M output tokens
cost_gpt5 = round((in_tok * 2.0 + out_tok * 8.0) / 1_000_000, 6)

print(f"\n📊 GPT-5.1 Stats:")
print(f"   Input tokens  : ~{in_tok}")
print(f"   Output tokens : ~{out_tok}")
print(f"   Estimated cost: ${cost_gpt5}")
print(f"   Response time : {time_gpt5}s")

# Save result
with open("/home/eden/eval_gpt5_result.json", "w") as f:
    json.dump({"model": "GPT-5.1", "response": text_gpt5,
               "time": time_gpt5, "cost": cost_gpt5,
               "input_tokens": in_tok, "output_tokens": out_tok}, f, indent=2)

print("\n✅ GPT-5.1 result saved. Now switch config to smart routing and run eval_smart.py")
