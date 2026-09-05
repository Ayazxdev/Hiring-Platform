# AI GitHunter — Standalone GitHub Profiler

A standalone Streamlit utility for batch repository auditing and candidate coding habit profiling using local Ollama LLMs.

## Overview

- **Profile Intelligence**: Analyzes commit regularity, recency, and activity bursts to classify candidate development velocity.
- **Repository Auditing**: Cross-references claimed competencies in `README.md` against actual installed dependencies (`package.json`, `requirements.txt`) and AST imports.
- **Batch Processing**: Accepts lists of GitHub profile URLs and runs parallel scraping to produce a comparative metrics table.

## Setup & Running

### 1. Prerequisites
- Python 3.10+
- Ollama running locally with `llama3.1`:
  ```bash
  ollama pull llama3.1
  ```

### 2. Install Dependencies
```bash
cd scraper
pip install -r requirements.txt
```

### 3. Launch Streamlit Dashboard
```bash
streamlit run main.py
```
Interface opens at `http://localhost:8501`.
