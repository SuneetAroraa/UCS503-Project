
## Text Simplification Engine

This project simplifies text using a rule-based engine and Google's Gemini API. It calculates readability metrics and compares the results of the two approaches.

### Features

- Rule-based text simplification
- Gemini-powered text simplification
- Hybrid mode with rule-based fallback
- Meaning checks for selected risks, including changed negations, numbers, and named entities
- Readability evaluation using Flesch Reading Ease, Flesch-Kincaid Grade Level, and SMOG Index
- Numerical comparison of original text, rule-based output, and Gemini output
- FastAPI endpoints for text processing

### Technology Stack

- Python
- spaCy
- textstat
- FastAPI and Pydantic
- Google Gen AI Python SDK
- unittest and pytest

### Setup

Create and activate a virtual environment, then install the required dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install fastapi uvicorn google-genai pytest httpx spacy textstat
python -m spacy download en_core_web_sm
```

### Configure Gemini

Create an API key using [Google AI Studio](https://aistudio.google.com/apikey).

Set it as an environment variable in your terminal:

```bash
export GEMINI_API_KEY="your-api-key"
```

Keep the key private. Do not commit it to GitHub.

The rule-based mode does not require a Gemini API key. Gemini and hybrid modes require the key and a working API connection.

### Run the API

From the project root:

```bash
python -m uvicorn code.python.api:app --reload
```

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

### API Endpoints

- `GET /health` — checks whether the API is running.
- `POST /simplify` — simplifies input text and returns readability metrics, comparisons, and an improvement summary.

Example request:

```json
{
  "text": "Although the application requires significant resources, it provides accessibility features that assist users.",
  "mode": "hybrid"
}
```

The `mode` field accepts:

- `rules` — uses the rule-based engine.
- `llm` — uses Gemini.
- `hybrid` — uses Gemini when the meaning check passes; otherwise, uses the rule-based result.

### Evaluation

The evaluation table compares word count, sentence count, average sentence length, Flesch Reading Ease, Flesch-Kincaid Grade Level, SMOG Index, and difficult-word count.

Readability formulas provide estimates; they do not prove that a rewrite preserves meaning or that readers understand it better. The meaning checker detects selected risks and cannot guarantee semantic equivalence.

### Testing

Run the unit tests:

```bash
python -m unittest discover -s tests -v
```

Run the API tests:

```bash
python -m pytest -p no:debugging -p no:cacheprovider -c /dev/null tests/test_api.py -v
```
