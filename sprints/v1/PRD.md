# Sprint v1 — PRD: PaperToCode

## Overview

Build a production-quality web application where researchers upload a paper PDF and receive a comprehensive, research-grade Google Colab notebook (.ipynb). The notebook goes beyond toy examples — it replicates key algorithms using realistic synthetic data, includes detailed mathematical derivations, step-by-step implementations, publication-quality visualizations, and exercises. Targeted at researchers at labs like OpenAI, DeepMind, and Google Brain who need to rapidly replicate and understand papers. Uses OpenAI's GPT-5.4 reasoning model for deep, structured analysis.

## Goals

- User uploads a research paper PDF (up to 50 MB)
- User enters their OpenAI API key once in the UI
- GPT-5.4 deeply analyzes the paper and generates a research-grade notebook with:
  - Paper summary with key contributions and novelty
  - Mathematical foundations (LaTeX in markdown cells)
  - Full algorithm implementations with realistic synthetic data
  - Publication-quality matplotlib/plotly visualizations
  - Ablation studies and hyperparameter sensitivity analysis
  - Exercises for deeper understanding
- User downloads the .ipynb file OR clicks "Open in Google Colab" to launch directly
- While generating, the UI shows live status messages to keep the user engaged (not a spinner — actual text like "Analyzing mathematical foundations...", "Implementing Algorithm 2...")
- UI/UX inspired by arcprize.org — clean, minimal, research-focused, authoritative

## User Stories

- As a research scientist at DeepMind, I want to upload a new paper and get a working implementation notebook in minutes, so I can evaluate whether to replicate the full paper
- As an ML engineer, I want the generated notebook to use realistic synthetic data and proper evaluation metrics, so the code is actually useful beyond a demo
- As a PhD student, I want detailed mathematical derivations alongside the code, so I can understand both the theory and implementation
- As a user, I want to see progress messages while the notebook generates, so I know the system is working and what stage it's at

## Technical Architecture

**Frontend**: Next.js 14 (App Router) + Tailwind CSS
**Backend**: FastAPI (Python)
**PDF Processing**: pdfplumber
**AI**: OpenAI GPT-5.4 reasoning model (via user-provided API key)
**Notebook Generation**: nbformat (Python)
**Design Theme**: Inspired by arcprize.org — dark/neutral palette, clean typography, research-grade aesthetic

```
┌──────────────────────────────────────────────────┐
│              Next.js Frontend                     │
│                                                   │
│  ┌──────────────────────────────────────────────┐ │
│  │  API Key Input (persisted in sessionStorage) │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │  PDF Upload Zone (drag-drop + browse)        │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │  Generate Button                             │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │  Live Status Feed (SSE stream)               │ │
│  │  "Extracting text from 24 pages..."          │ │
│  │  "Identifying 3 key algorithms..."           │ │
│  │  "Implementing Algorithm 1: Attention..."    │ │
│  │  "Generating synthetic dataset..."           │ │
│  │  "Building evaluation metrics..."            │ │
│  └──────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────┐ │
│  │  Download .ipynb  |  Open in Google Colab    │ │
│  └──────────────────────────────────────────────┘ │
└───────────────────────┬──────────────────────────┘
                        │ POST /api/convert (multipart)
                        │ GET  /api/status/{job_id} (SSE)
                        ▼
┌──────────────────────────────────────────────────┐
│              FastAPI Backend                       │
│                                                   │
│  1. Extract text from PDF (pdfplumber)            │
│  2. Analyze paper structure (GPT-5.4)             │
│  3. Generate notebook JSON (GPT-5.4 reasoning)    │
│     - Summary + key contributions                 │
│     - Math foundations (LaTeX)                     │
│     - Algorithm implementations                   │
│     - Synthetic data generation                   │
│     - Visualizations + evaluation                 │
│     - Exercises                                   │
│  4. Build .ipynb (nbformat)                       │
│  5. Return notebook + emit status events (SSE)    │
└──────────────────────────────────────────────────┘
```

**Data Flow**:
1. User enters OpenAI API key (stored in sessionStorage, never sent to our servers)
2. User drops a research paper PDF
3. Frontend POSTs multipart form (file + api_key) to FastAPI `/api/convert`
4. Backend extracts text, emits status event: "Extracting text..."
5. Backend sends text to GPT-5.4 with a deep structured prompt, emits progress
6. GPT-5.4 returns structured JSON: summary, math, algorithms, data generation, visualizations, exercises
7. Backend builds .ipynb using nbformat, emits "Building notebook..."
8. Frontend receives the .ipynb and shows download + "Open in Colab" buttons
9. "Open in Colab" works by uploading the notebook to a GitHub Gist (via user's browser) and redirecting to `colab.research.google.com/gist/...`

**Live Status Feed (SSE)**:
- Backend emits Server-Sent Events during generation
- Frontend listens and displays each message in a feed
- Messages are specific and informative, e.g.:
  - "Extracting text from 24 pages..."
  - "Identified paper: 'Attention Is All You Need' (Vaswani et al., 2017)"
  - "Analyzing 3 key algorithms: Multi-Head Attention, Positional Encoding, Feed-Forward Network"
  - "Implementing Algorithm 1: Scaled Dot-Product Attention..."
  - "Generating synthetic sequence-to-sequence dataset (10K samples)..."
  - "Building evaluation pipeline with BLEU score metrics..."
  - "Notebook ready — 47 cells, 12 code blocks"

**Notebook Structure (what GPT-5.4 generates)**:
1. Title + metadata (paper title, authors, date, link)
2. Executive summary (key contributions, novelty, impact)
3. Prerequisites + pip installs
4. Mathematical foundations (LaTeX equations with explanations)
5. Algorithm implementations (each major algorithm as a section):
   - Pseudocode explanation
   - Python implementation with type hints and docstrings
   - Unit test cell to verify correctness
6. Synthetic data generation (realistic, not random noise)
7. Training / execution pipeline
8. Evaluation + visualizations (matplotlib/plotly, publication-quality)
9. Ablation study (vary key hyperparameters, show impact)
10. Exercises (3-5 meaningful challenges, not trivial)
11. References + further reading

## Design Direction

Inspired by arcprize.org:
- **Palette**: Dark background (#0a0a0a or near-black), white/light gray text, subtle accent color (muted blue or teal)
- **Typography**: Clean sans-serif (Inter or similar), monospace for code references, strong heading hierarchy
- **Layout**: Centered single-column, generous whitespace, minimal chrome
- **Vibe**: Authoritative, research-grade, no gimmicks — feels like a tool built by researchers for researchers
- **Interactions**: Subtle transitions, no flashy animations, focus on content

## Out of Scope (v2+)

- User accounts / authentication / usage tracking
- ArXiv URL input (fetch paper by URL/ID)
- Multiple AI provider support (Claude, Gemini)
- Customizable notebook sections
- Saved history of generated notebooks
- Rate limiting and abuse prevention
- Team/organization features
- Deployment infrastructure (Docker, CI/CD)

## Dependencies

- None (greenfield project)
