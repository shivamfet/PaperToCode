# Sprint v1 — Tasks

## Status: In Progress

- [x] Task 1: Initialize Next.js 14 project with Tailwind CSS and ARC-inspired theme (P0)
  - Acceptance: `npm run dev` starts without errors. Global styles set dark background (#0a0a0a), light text, Inter font, CSS variables for the theme palette. Layout has centered single-column structure with generous whitespace.
  - Files: package.json, tailwind.config.ts, app/layout.tsx, app/page.tsx, app/globals.css
  - Completed: 2026-03-25 — Next.js 14 with React 18, Tailwind 3, ARC dark theme, centered layout. 10 tests passing (vitest). Used yarn due to npm registry access issues.

- [x] Task 2: Initialize FastAPI backend with project structure and health check (P0)
  - Acceptance: `uvicorn main:app --reload` starts on port 8000. `GET /health` returns `{"status": "ok"}`. CORS configured to allow Next.js dev origin. Directory structure has services/ package.
  - Files: backend/main.py, backend/requirements.txt, backend/services/__init__.py
  - Completed: 2026-03-25 — FastAPI 0.135.2 with health endpoint, CORS for localhost:3000, services/ package. 4 tests passing (pytest). pip-audit clean, semgrep clean.

- [ ] Task 3: Build the main UI — API key input, PDF upload zone, generate button (P0)
  - Acceptance: Page has API key input (stored in sessionStorage, show/hide toggle), drag-drop PDF upload zone with file preview and remove, and a "Generate Notebook" button disabled until both fields are filled. Matches ARC-inspired dark theme.
  - Files: app/page.tsx, app/components/ApiKeyInput.tsx, app/components/UploadZone.tsx, app/components/GenerateButton.tsx

- [ ] Task 4: Implement PDF text extraction service (P0)
  - Acceptance: `extract_text_from_pdf(file_bytes)` returns full text with page markers. Raises ValueError for scanned/image PDFs with no extractable text. Handles large PDFs (50+ pages).
  - Files: backend/services/pdf_extractor.py

- [ ] Task 5: Implement GPT-5.4 research notebook generation service (P0)
  - Acceptance: `generate_tutorial(pdf_text, api_key)` calls GPT-5.4 with a structured prompt and returns a dict with: title, authors, summary, math_foundations, algorithms (each with pseudocode + implementation + synthetic data), visualizations, ablation_study, exercises, references. Uses `.replace()` for prompt substitution (not `.format()`). Handles API errors gracefully.
  - Files: backend/services/openai_service.py

- [ ] Task 6: Implement research-grade notebook builder (P0)
  - Acceptance: `build_notebook(tutorial_data)` produces a valid .ipynb with: title cell, executive summary, pip installs, LaTeX math cells, algorithm implementation cells with type hints, synthetic data generation, evaluation + plotting cells, ablation study, exercises, and references. `notebook_to_bytes(nb)` returns UTF-8 JSON bytes. Notebook opens in Colab without errors.
  - Files: backend/services/notebook_builder.py

- [ ] Task 7: Create POST /api/convert endpoint with SSE status streaming (P0)
  - Acceptance: POST `/api/convert` with multipart form (file + openai_api_key) processes the PDF and returns a downloadable .ipynb. During processing, SSE events stream to `/api/status/{job_id}` with descriptive messages (e.g. "Extracting text from 24 pages..."). Returns 400 for invalid files, 401 for bad API keys, 500 for failures. Job ID returned immediately so frontend can subscribe to SSE.
  - Files: backend/main.py (update), backend/services/job_manager.py

- [ ] Task 8: Build live status feed and download/Colab UI (P1)
  - Acceptance: After clicking Generate, frontend subscribes to SSE and displays status messages in a feed (styled like a terminal log). On completion, shows two buttons: "Download .ipynb" and "Open in Google Colab". Colab button creates a GitHub Gist with the notebook content and opens `colab.research.google.com/gist/...` in a new tab. If Gist creation fails, falls back to download only.
  - Files: app/page.tsx (update), app/components/StatusFeed.tsx, app/components/DownloadSection.tsx

- [ ] Task 9: Configure Next.js proxy to FastAPI and production build (P1)
  - Acceptance: Next.js dev server proxies `/api/*` requests to FastAPI on port 8000. `npm run build` succeeds with no errors. Both servers can be started with a single README command.
  - Files: next.config.js, README.md (setup instructions)

- [ ] Task 10: Polish UI — responsive layout, error handling, empty states (P2)
  - Acceptance: Layout works on mobile (375px+). Error messages are clear and specific for every failure mode (bad API key, invalid PDF, network error). Status feed has smooth scroll and auto-scroll to latest message. Loading states on all async operations.
  - Files: app/page.tsx, app/components/*.tsx (various updates)
