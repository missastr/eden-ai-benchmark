import os, requests, time, json, subprocess
from dotenv import load_dotenv

load_dotenv()
EDEN_API_KEY = os.getenv("EDENAI_API_KEY")

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
    body = {
        "providers": "openai/gpt-5",
        "text": compressed,
        "chatbot_global_action": "You are a helpful assistant.",
        "previous_history": [],
        "temperature": 0.0,
        "max_tokens": 1000,
    }
    headers = {"Authorization": f"Bearer {EDEN_API_KEY}", "Content-Type": "application/json"}
    start = time.time()
    resp  = requests.post("https://api.edenai.run/v2/text/chat", headers=headers, json=body, timeout=90)
    elapsed = round(time.time() - start, 1)
    data = resp.json()
    r    = data.get("openai/gpt-5", {})
    if r.get("status") == "success":
        usage = r.get("usage", {})
        return r.get("generated_text", ""), elapsed, r.get("cost", 0), usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), compressed
    return "ERROR", elapsed, 0, 0, 0, compressed

print("Model: GPT-5 + LLMLingua\n" + "=" * 50)

total_cost = total_time = 0
for task in TASKS:
    content, elapsed, cost, in_tok, out_tok, compressed = run(task["prompt"])
    total_cost += cost
    total_time += elapsed
    print(f"\n[{task['type']}]")
    print(f"  Original prompt  : {task['prompt'][:80]}...")
    print(f"  Compressed prompt: {compressed[:80]}...")
    print(f"  Time   : {elapsed}s")
    print(f"  Tokens : {out_tok} output / {in_tok} input")
    print(f"  Cost   : ${cost:.6f}")
    print(f"  Answer : {content.strip()[:150]}")
    time.sleep(1)

print(f"\n{'=' * 50}")
print(f"Total cost : ${total_cost:.6f}")
print(f"Total time : {total_time}s")
