import os, requests, time, subprocess
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("EDENAI_API_KEY")
URL     = "https://api.edenai.run/v3/llm/chat/completions"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

ROUTER_CANDIDATES = [
    "openai/gpt-4o",
    "openai/gpt-4.1",
    "openai/gpt-4.1-mini",
    "openai/gpt-4o-mini",
    "openai/gpt-4.1-nano",
    "anthropic/claude-3-haiku-20240307",
    "mistral/mistral-large-latest",
    "mistral/mistral-small-latest",
    "google/gemini-2.0-flash",
    "mistral/mistral-medium-latest",
]

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

PRICING = {
    "google/gemini-2.0-flash":           {"input": 0.10, "output": 0.40},
    "openai/gpt-4o-mini":                {"input": 0.15, "output": 0.60},
    "openai/gpt-4.1-mini":               {"input": 0.40, "output": 1.60},
    "anthropic/claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "mistral/mistral-small-latest":      {"input": 0.10, "output": 0.30},
    "default":                           {"input": 0.10, "output": 0.40},
}

def get_price(model, in_tok, out_tok):
    p = PRICING.get(model, PRICING["default"])
    return (in_tok * p["input"] + out_tok * p["output"]) / 1_000_000

def compress(prompt):
    result = subprocess.run(
        ["/home/eden/llmlingua-env/bin/python", "-c",
         f"""
from llmlingua import PromptCompressor
c = PromptCompressor("microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank", use_llmlingua2=True, device_map="cpu")
r = c.compress_prompt("{prompt.replace(chr(34), chr(39))}", rate=0.5)
print(r["compressed_prompt"])
"""],
        capture_output=True, text=True, timeout=60
    )
    return result.stdout.strip() or prompt

def run(prompt):
    compressed = compress(prompt)
    start = time.time()
    resp  = requests.post(URL, headers=HEADERS, json={
        "model": "@edenai",
        "messages": [{"role": "user", "content": compressed}],
        "max_tokens": 400,
        "router_candidates": ROUTER_CANDIDATES,
    }, timeout=60)
    elapsed    = round(time.time() - start, 1)
    data       = resp.json()
    model_used = data.get("model", "@edenai")
    content    = data.get("choices", [{}])[0].get("message", {}).get("content", "ERROR")
    usage      = data.get("usage", {})
    in_tok     = usage.get("prompt_tokens", 0)
    out_tok    = usage.get("completion_tokens", 0)
    cost       = get_price(model_used, in_tok, out_tok)
    return content, elapsed, cost, in_tok, out_tok, model_used, compressed

print("Model: Smart Routing (10 models) + LLMLingua\n" + "=" * 50)

total_cost = total_time = 0
for task in TASKS:
    content, elapsed, cost, in_tok, out_tok, model_used, compressed = run(task["prompt"])
    total_cost += cost
    total_time += elapsed
    print(f"\n[{task['type']}]")
    print(f"  Original prompt  : {task['prompt'][:80]}...")
    print(f"  Compressed prompt: {compressed[:80]}...")
    print(f"  Model picked     : {model_used}")
    print(f"  Time   : {elapsed}s")
    print(f"  Tokens : {out_tok} output / {in_tok} input")
    print(f"  Cost   : ${cost:.6f}")
    print(f"  Answer : {content.strip()[:150]}")
    time.sleep(1)

print(f"\n{'=' * 50}")
print(f"Total cost : ${total_cost:.6f}")
print(f"Total time : {total_time}s")
