# PaperToCode

Upload a research paper PDF and get a research-grade Google Colab notebook with algorithm implementations, visualizations, and exercises. Powered by GPT-5.4.

## Prerequisites

- Node.js 18+ and Yarn
- Python 3.10+
- An OpenAI API key (entered in the UI, stored in sessionStorage)

## Setup

### Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (Next.js)

```bash
yarn install
yarn dev
```

The Next.js dev server runs on `http://localhost:3000` and proxies all `/api/*` requests to the FastAPI backend on port `8000`.

## Quick Start (both servers)

In two terminal tabs:

```bash
# Tab 1: Backend
cd backend && uvicorn main:app --reload --port 8000

# Tab 2: Frontend
yarn dev
```

Then open `http://localhost:3000`.

## Running Tests

```bash
# Frontend (vitest)
npx vitest run

# Backend (pytest)
cd backend && python -m pytest tests/ -v
```

## Production Build

```bash
yarn build
yarn start
```
