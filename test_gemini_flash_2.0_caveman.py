import os, requests, time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("EDENAI_API_KEY")
URL     = "https://api.edenai.run/v3/llm/chat/completions"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

CAVEMAN_PREFIX = "Talk like caveman. Be ultra terse. Drop articles and filler. Keep all technical accuracy. "

TASKS = [
    {"type": "Simple",
     "prompt": "Write a one sentence Reddit comment agreeing that Breaking Bad is a great show."},
    {"type": "Creative",
     "prompt": ("You are a Reddit user in r/movies. Write a passionate 4-5 sentence comment "
                "recommending an underrated film masterpiece. Sound like a genuine film enthusiast.")},
    {"type": "Analytical",
     "prompt": ("You are a Reddit user in r/anime. A post asks: 'Why do so many anime have "
                "unsatisfying endings?' Write a thoughtful 3-4 sentence reply with your analysis.")},
    {"type": "Conversational",
     "prompt": ("You are a Reddit user in r/television. Someone asked for the most addictive "
                "TV series ever. Write a natural 2-3 sentence reply recommending your pick and why.")},
    {"type": "Complex",
     "prompt": ("You are a Reddit user in r/TurkishDrama. Write a detailed 5-sentence comment "
                "comparing the storytelling style of Turkish dramas vs Western series, "
                "mentioning specific shows as examples. Sound knowledgeable and passionate.")},
]

def run(prompt):
    start = time.time()
    resp  = requests.post(URL, headers=HEADERS, json={
        "model": "google/gemini-2.0-flash",
        "messages": [{"role": "user", "content": CAVEMAN_PREFIX + prompt}],
        "max_tokens": 400,
    }, timeout=60)
    elapsed = round(time.time() - start, 1)
    data    = resp.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "ERROR")
    usage   = data.get("usage", {})
    in_tok  = usage.get("prompt_tokens", 0)
    out_tok = usage.get("completion_tokens", 0)
    cost    = (in_tok * 0.10 + out_tok * 0.40) / 1_000_000
    return content, elapsed, cost, in_tok, out_tok

print("Model: Gemini Flash 2.0 + Caveman Mode\n" + "=" * 50)

total_cost = total_time = 0
for task in TASKS:
    content, elapsed, cost, in_tok, out_tok = run(task["prompt"])
    total_cost += cost
    total_time += elapsed
    print(f"\n[{task['type']}]")
    print(f"  Time   : {elapsed}s")
    print(f"  Tokens : {out_tok} output / {in_tok} input")
    print(f"  Cost   : ${cost:.6f}")
    print(f"  Answer : {content.strip()[:150]}")
    time.sleep(1)

print(f"\n{'=' * 50}")
print(f"Total cost : ${total_cost:.6f}")
print(f"Total time : {total_time}s")
