# Eden AI  Benchmark: LLMLingua & Caveman Mode

Benchmarking two token compression techniques across GPT-5, Gemini Flash 2.0, and Smart Routing on Eden AI.

## Tools Tested
- **LLMLingua**  Compresses input prompts before sending (Microsoft)
- **Caveman Mode**  Instructs the model to respond in ultra-terse fragments

## Models
- GPT-5
- Gemini Flash 2.0
- Smart Routing (Eden AI fallback routing)

## Files
| File | Description |
|------|-------------|
| `benchmark.py` | LLMLingua benchmark — 5 tasks × 3 models × normal/compressed |
| `benchmark_caveman.py` | Caveman mode benchmark — same structure |
| `generate_pdf.py` | Generates PDF report for LLMLingua results |
| `generate_caveman_pdf.py` | Generates PDF report for Caveman results |
| `benchmark_article.html` | Full HTML article with both results and conclusions |
| `test_compress.py` | Interactive LLMLingua compression test |

## Setup
```bash
pip install llmlingua python-dotenv requests reportlab
```

Create a `.env` file (never commit this):
```
EDENAI_API_KEY=your_key_here
```

## Run
```bash
python benchmark.py        # LLMLingua benchmark
python benchmark_caveman.py  # Caveman mode benchmark
```

---
Eden AI Internship — April 2026
