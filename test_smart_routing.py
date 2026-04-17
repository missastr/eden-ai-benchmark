import requests, json, time

import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("EDENAI_API_KEY")
URL     = "https://api.edenai.run/v3/llm/chat/completions"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# ── 10 mid-tier balanced models (cost + quality) ──────────────────────────────
ROUTER_CANDIDATES = [
    "openai/gpt-4o",                     # equal quality to GPT-5.1, 40% faster, 5% cheaper
    "openai/gpt-4.1",                    # 27% cheaper, 54% faster, close quality
    "openai/gpt-4.1-mini",               # 85% cheaper, 55% faster, near equal quality
    "openai/gpt-4o-mini",                # 95% cheaper, 53% faster, solid quality
    "openai/gpt-4.1-nano",               # cheapest OpenAI, ultra fast
    "anthropic/claude-3-haiku-20240307", # 85% cheaper, 59% fastest overall
    "mistral/mistral-large-latest",      # 22% cheaper, 15% faster, good quality
    "mistral/mistral-small-latest",      # cheap + fast Mistral
    "google/gemini-2.0-flash",           # ultra fast, ultra cheap
    "mistral/mistral-medium-latest",     # balanced Mistral fallback
]

# ── 5 tasks ───────────────────────────────────────────────────────────────────
TASKS = [
    {"id": 1, "type": "Simple",
     "prompt": "Write a one sentence Reddit comment agreeing that Breaking Bad is a great show."},
    {"id": 2, "type": "Creative",
     "prompt": ("You are a Reddit user in r/movies. Write a passionate 4-5 sentence comment "
                "recommending an underrated film masterpiece. Sound like a genuine film enthusiast.")},
    {"id": 3, "type": "Analytical",
     "prompt": ("You are a Reddit user in r/anime. A post asks: 'Why do so many anime have "
                "unsatisfying endings?' Write a thoughtful 3-4 sentence reply with your analysis.")},
    {"id": 4, "type": "Conversational",
     "prompt": ("You are a Reddit user in r/television. Someone asked for the most addictive "
                "TV series ever. Write a natural 2-3 sentence reply recommending your pick and why.")},
    {"id": 5, "type": "Complex",
     "prompt": ("You are a Reddit user in r/TurkishDrama. Write a detailed 5-sentence comment "
                "comparing the storytelling style of Turkish dramas vs Western series, "
                "mentioning specific shows as examples. Sound knowledgeable and passionate.")},
]

PRICING = {
    "openai/gpt-5.1-2025-11-13":  {"input": 2.00,  "output": 8.00},
    "openai/gpt-4o-mini":         {"input": 0.15,  "output": 0.60},
    "anthropic/claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "google/gemini-2.5-flash":    {"input": 0.15,  "output": 0.60},
    "google/gemini-2.0-flash":    {"input": 0.10,  "output": 0.40},
    "mistral/mistral-small-latest": {"input": 0.10, "output": 0.30},
    "groq/llama-3.3-70b-versatile": {"input": 0.05, "output": 0.08},
    "deepseek/deepseek-chat":     {"input": 0.07,  "output": 0.28},
    "default":                    {"input": 0.10,  "output": 0.40},
}

def get_price(model, in_tok, out_tok):
    p = PRICING.get(model, PRICING["default"])
    return (in_tok * p["input"] + out_tok * p["output"]) / 1_000_000

def score_response(text, task_type):
    if not text or "ERROR" in text:
        return 0
    words    = len(text.split())
    complete = 1 if text[-1] in ".!?" else 0
    min_words = {"Simple": 5, "Creative": 60, "Analytical": 50,
                 "Conversational": 30, "Complex": 80}
    length_ok = 1 if words >= min_words.get(task_type, 20) else 0
    base = 6 if (complete and length_ok) else 3 if (complete or length_ok) else 1
    if words > 100: base = min(base + 2, 10)
    elif words > 50: base = min(base + 1, 10)
    return base

def run_model(model_id, prompt, candidates=None):
    try:
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
        }
        if candidates:
            payload["router_candidates"] = candidates

        start    = time.time()
        response = requests.post(URL, headers=HEADERS, json=payload, timeout=60)
        elapsed  = round(time.time() - start, 1)
        data     = response.json()
        model_used = data.get("model", model_id)
        content    = data.get("choices", [{}])[0].get("message", {}).get("content", "ERROR")
        usage      = data.get("usage", {})
        in_tok     = usage.get("prompt_tokens", len(prompt) // 4)
        out_tok    = usage.get("completion_tokens", len(content) // 4)
        cost       = get_price(model_used, in_tok, out_tok)
        return {"model_used": model_used, "response": content,
                "time": elapsed, "input_tokens": in_tok,
                "output_tokens": out_tok, "cost": cost, "error": False}
    except Exception as e:
        return {"model_used": model_id, "response": "ERROR",
                "time": 0, "input_tokens": 0, "output_tokens": 0,
                "cost": 0, "error": True}

# ── Run benchmark ─────────────────────────────────────────────────────────────
print("=" * 70)
print("   BENCHMARK: GPT-5.1  vs  Smart Routing v2 (10 balanced candidates)")
print("   Tasks: 5  |  Same prompts sent to both")
print("=" * 70)

results_gpt   = []
results_smart = []

for task in TASKS:
    print(f"\n[Task {task['id']} — {task['type']}]")

    print(f"  Running GPT-5.1...", end=" ", flush=True)
    r_gpt = run_model("openai/gpt-5.1-2025-11-13", task["prompt"])
    r_gpt["score"] = score_response(r_gpt["response"], task["type"])
    results_gpt.append(r_gpt)
    print(f"done ({r_gpt['time']}s | ${r_gpt['cost']:.6f} | score {r_gpt['score']}/10)")

    time.sleep(2)

    print(f"  Running Smart Routing v2...", end=" ", flush=True)
    r_smart = run_model("@edenai", task["prompt"], candidates=ROUTER_CANDIDATES)
    r_smart["score"] = score_response(r_smart["response"], task["type"])
    results_smart.append(r_smart)
    print(f"done ({r_smart['time']}s | ${r_smart['cost']:.6f} | score {r_smart['score']}/10) → picked: {r_smart['model_used']}")

    time.sleep(2)

# ── Totals ────────────────────────────────────────────────────────────────────
total_cost_gpt   = sum(r["cost"]  for r in results_gpt)
total_cost_smart = sum(r["cost"]  for r in results_smart)
total_time_gpt   = sum(r["time"]  for r in results_gpt)
total_time_smart = sum(r["time"]  for r in results_smart)
avg_score_gpt    = round(sum(r["score"] for r in results_gpt)  / len(TASKS), 1)
avg_score_smart  = round(sum(r["score"] for r in results_smart)/ len(TASKS), 1)

cost_saving_pct  = round((1 - total_cost_smart / total_cost_gpt) * 100, 1) if total_cost_gpt > 0 else 0
time_diff_pct    = round((1 - total_time_smart / total_time_gpt) * 100, 1) if total_time_gpt > 0 else 0
quality_diff_pct = round((avg_score_smart / avg_score_gpt - 1) * 100, 1)   if avg_score_gpt  > 0 else 0

# ── Table ─────────────────────────────────────────────────────────────────────
print("\n\n" + "=" * 70)
print("   DETAILED RESULTS PER TASK")
print("=" * 70)
print(f"{'Task':<22} {'GPT-5.1':>8} {'Smart v2':>10} {'GPT cost':>10} {'Smart cost':>11} {'GPT score':>10} {'Smart score':>12}")
print("-" * 70)
for i, task in enumerate(TASKS):
    rg = results_gpt[i]
    rs = results_smart[i]
    print(f"{task['type']:<22} {str(rg['time'])+'s':>8} {str(rs['time'])+'s':>10} "
          f"${rg['cost']:.6f} ${rs['cost']:.6f}  "
          f"{str(rg['score'])+'/10':>10} {str(rs['score'])+'/10':>12}")

print("\n" + "=" * 70)
print("   MODELS PICKED BY SMART ROUTING v2")
print("=" * 70)
for i, task in enumerate(TASKS):
    print(f"  Task {task['id']} ({task['type']:<14}): {results_smart[i]['model_used']}")

print("\n" + "=" * 70)
print("   FINAL SUMMARY")
print("=" * 70)
print(f"{'Metric':<30} {'GPT-5.1':>15} {'Smart v2':>15}")
print("-" * 65)
print(f"{'Total cost (5 tasks)':<30} {'$'+f'{total_cost_gpt:.6f}':>15} {'$'+f'{total_cost_smart:.6f}':>15}")
print(f"{'Total time':<30} {str(total_time_gpt)+'s':>15} {str(total_time_smart)+'s':>15}")
print(f"{'Avg quality score':<30} {str(avg_score_gpt)+'/10':>15} {str(avg_score_smart)+'/10':>15}")
print("-" * 65)
print(f"\n  💰 Cost saving   : {cost_saving_pct}% cheaper")
print(f"  ⚡ Speed          : {abs(time_diff_pct)}% {'faster' if time_diff_pct > 0 else 'slower'}")
print(f"  📊 Quality        : {abs(quality_diff_pct)}% {'better' if quality_diff_pct > 0 else 'lower'} quality")

winner_cost    = "Smart v2" if total_cost_smart < total_cost_gpt else "GPT-5.1"
winner_speed   = "Smart v2" if total_time_smart < total_time_gpt else "GPT-5.1"
winner_quality = "GPT-5.1" if avg_score_gpt >= avg_score_smart else "Smart v2"

print(f"\n  ✅ Best for cost    : {winner_cost}")
print(f"  ✅ Best for speed   : {winner_speed}")
print(f"  ✅ Best for quality : {winner_quality}")
print("=" * 70)
