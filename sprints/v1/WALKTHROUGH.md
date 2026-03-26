# Sprint v1 — Walkthrough

## Summary

Sprint v1 built the complete PaperToCode application from scratch: a Next.js 14 frontend with an ARC-inspired dark theme and a FastAPI backend that extracts text from research paper PDFs, sends it to GPT-5.4 for deep analysis, and produces a research-grade Jupyter notebook (.ipynb) with algorithm implementations, mathematical derivations, visualizations, and exercises. The full pipeline — from PDF upload through live status updates to notebook download or direct Colab launch — is functional. 117 tests (52 frontend, 65 backend) cover all components with zero security findings.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                 Next.js 14 Frontend                  │
│                  (localhost:3000)                     │
│                                                      │
│  ┌────────────┐ ┌────────────┐ ┌──────────────────┐ │
│  │ ApiKeyInput│ │ UploadZone │ │ GenerateButton   │ │
│  │ (session-  │ │ (drag-drop │ │ (disabled until  │ │
│  │  Storage)  │ │  + browse) │ │  both filled)    │ │
│  └────────────┘ └────────────┘ └──────────────────┘ │
│  ┌──────────────────────────────────────────────────┐│
│  │ StatusFeed (terminal-style polling log)          ││
│  └──────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────┐│
│  │ DownloadSection (.ipynb download | Open in Colab)││
│  └──────────────────────────────────────────────────┘│
└─────────────────────┬────────────────────────────────┘
                      │  next.config.js rewrites
                      │  /api/* → localhost:8000/api/*
                      ▼
┌─────────────────────────────────────────────────────┐
│                FastAPI Backend                        │
│                (localhost:8000)                       │
│                                                      │
│  POST /api/convert ──→ JobManager.create_job()       │
│       │                    │                         │
│       └─ background ───────┘                         │
│          thread                                      │
│            │                                         │
│            ├─ pdf_extractor.extract_text_from_pdf()  │
│            ├─ openai_service.generate_tutorial()     │
│            └─ notebook_builder.build_notebook()      │
│                                                      │
│  GET /api/status/{job_id} ──→ poll messages + status │
│  GET /api/download/{job_id} ──→ .ipynb bytes         │
│  GET /health ──→ {"status": "ok"}                    │
└─────────────────────────────────────────────────────┘
```

## Files Created/Modified

### app/globals.css
**Purpose**: CSS custom properties defining the ARC-inspired dark theme palette.
**Key Variables**:
- `--background: #0a0a0a` — Near-black page background
- `--accent: #4a9ead` — Muted teal for interactive elements
- `--surface: #141414` — Slightly elevated card/input backgrounds
- `--border: #262626` — Subtle borders

**How it works**:
The CSS variables are defined on `:root` and consumed by both Tailwind (via `tailwind.config.ts` color mappings) and direct CSS usage. The `::selection` rule uses the accent color so even text selection feels on-brand. Inter is the primary font with system-ui fallback, and font smoothing is enabled for crisp rendering on macOS/Linux.

### tailwind.config.ts
**Purpose**: Extends Tailwind with the custom color palette and font families.
**Key Config**:
- `colors` maps theme variables (`background`, `accent`, `surface`, etc.) to hex values
- `fontFamily.sans` uses Inter; `fontFamily.mono` uses JetBrains Mono for the status feed

**How it works**:
By extending `theme.colors`, components can use classes like `bg-surface`, `text-accent`, `border-border` directly. This keeps the dark theme consistent without repeating hex codes. The `content` array scans `app/` and `components/` for Tailwind class usage during tree-shaking.

### app/layout.tsx
**Purpose**: Root layout with centered single-column structure and responsive padding.
**Key Elements**:
- `<main>` with `min-h-screen`, centered flex layout
- `max-w-2xl` content container
- Responsive: `px-4 sm:px-6`, `py-8 sm:py-16`

**How it works**:
Every page renders inside this layout. On mobile (375px+), padding is tighter (px-4, py-8) to maximize content space. At the `sm` breakpoint (640px), padding increases for a more spacious desktop feel. The `max-w-2xl` (672px) keeps content readable without stretching too wide on large screens.

### app/page.tsx
**Purpose**: Main application page orchestrating the full generate flow.
**Key State**:
- `apiKey`, `file` — user inputs
- `jobId`, `messages`, `error` — job lifecycle
- `isGenerating`, `isComplete` — UI state flags

**How it works**:
The page manages the entire user journey. When the user clicks Generate, `handleGenerate()` POSTs a `FormData` with the PDF file and API key to `/api/convert`. The backend returns a `job_id` immediately. The page then starts polling `/api/status/{job_id}` every second via `setInterval`. Each poll updates the `messages` array displayed in the StatusFeed. When the job status becomes `"completed"`, polling stops and the DownloadSection appears. If it becomes `"failed"`, the error is displayed — with special handling for `AUTH:` prefixed errors (shown as "Invalid API key").

```typescript
const pollStatus = useCallback((id: string) => {
  pollRef.current = setInterval(async () => {
    const resp = await fetch(`/api/status/${id}`);
    const data = await resp.json();
    setMessages(data.messages || []);
    if (data.status === "completed") {
      stopPolling();
      setIsComplete(true);
    } else if (data.status === "failed") {
      stopPolling();
      setError(data.error?.startsWith("AUTH:")
        ? "Invalid API key. Please check and try again."
        : data.error || "Generation failed.");
    }
  }, POLL_INTERVAL);
}, [stopPolling]);
```

The `canGenerate` flag disables the button when either field is empty OR when a generation is already in progress, preventing duplicate submissions.

### app/components/ApiKeyInput.tsx
**Purpose**: Password-style input for the OpenAI API key with show/hide toggle.
**Key Props**: `value: string`, `onChange: (value: string) => void`
**Test IDs**: `api-key-input`, `api-key-toggle`

**How it works**:
Renders a standard `<input>` that toggles between `type="password"` and `type="text"` via a "Show"/"Hide" button. The parent component (`page.tsx`) handles persisting the value to `sessionStorage` on every change, so the key survives page refreshes within the same tab but is never written to localStorage or sent to any server other than OpenAI (via the backend proxy).

### app/components/UploadZone.tsx
**Purpose**: Drag-and-drop PDF upload area with file preview and remove button.
**Key Props**: `file: File | null`, `onFile: (file: File) => void`, `onRemove: () => void`
**Test IDs**: `upload-zone`, `file-input`, `remove-file`

**How it works**:
Has two visual states. **Empty state**: a dashed-border drop zone with "Drag & drop a PDF here, or browse" text. Clicking anywhere opens the hidden `<input type="file">`. Dragging over the zone changes the border to accent color via `dragOver` state. **File selected state**: shows the filename, size in KB, and a "Remove" button. Only `application/pdf` files are accepted — both the `accept` attribute and a runtime `type` check enforce this.

### app/components/GenerateButton.tsx
**Purpose**: Primary action button with loading state.
**Key Props**: `disabled: boolean`, `loading?: boolean`, `onClick: () => void`
**Test ID**: `generate-button`

**How it works**:
When `loading` is true, the button text changes from "Generate Notebook" to "Generating..." and it's visually disabled. The `disabled` prop covers both the "fields not filled" and "already generating" cases. Styled with the accent color, with reduced opacity when disabled.

### app/components/StatusFeed.tsx
**Purpose**: Terminal-style log showing live status messages during generation.
**Key Props**: `messages: string[]`, `error?: string | null`
**Test IDs**: `status-feed`, `status-message`, `status-error`

**How it works**:
Renders each message as a line prefixed with a teal `›` character in a monospace font. A `useEffect` auto-scrolls to the bottom div whenever `messages.length` changes, using `scrollIntoView({ behavior: "smooth" })` (with a guard for jsdom test environments). Errors render in red with a `✕` prefix. The container has `max-h-64 overflow-y-auto` so it becomes scrollable when messages exceed the visible area.

### app/components/DownloadSection.tsx
**Purpose**: Post-generation actions — download .ipynb or open in Google Colab.
**Key Props**: `visible: boolean`, `jobId: string`
**Test IDs**: `download-section`, `download-button`, `colab-button`

**How it works**:
The download button is a simple `<a>` tag pointing to `/api/download/{jobId}` with a `download` attribute. The Colab button is more complex: it fetches the notebook content, creates an anonymous GitHub Gist via `api.github.com/gists`, then opens `colab.research.google.com/gist/{owner}/{id}/notebook.ipynb` in a new tab. If Gist creation fails (e.g., rate limit, no GitHub auth), it sets `colabError` and the button text changes to "Gist failed — Download instead". On mobile, the buttons stack vertically (`flex-col sm:flex-row`).

### backend/main.py
**Purpose**: FastAPI application with three API endpoints and CORS configuration.
**Key Endpoints**:
- `GET /health` — returns `{"status": "ok"}`
- `POST /api/convert` — accepts multipart form, returns `{"job_id": "..."}`
- `GET /api/status/{job_id}` — returns job status, messages, and error
- `GET /api/download/{job_id}` — returns .ipynb bytes

**How it works**:
The `/api/convert` endpoint validates the uploaded file is a PDF (by filename extension), reads its bytes, creates a job in the `JobManager`, and kicks off `_process_job()` in a background thread via `run_in_executor`. This returns the `job_id` immediately so the frontend can start polling.

The `_process_job` function runs the full pipeline sequentially, emitting descriptive status messages at each step:

```python
def _process_job(job_id, file_bytes, api_key):
    job_manager.add_message(job_id, "Extracting text from PDF...")
    pdf_text = extract_text_from_pdf(file_bytes)

    job_manager.add_message(job_id, "Analyzing paper with GPT-5.4...")
    tutorial_data = generate_tutorial(pdf_text, api_key)

    job_manager.add_message(job_id, "Building research notebook...")
    nb = build_notebook(tutorial_data)
    nb_bytes = notebook_to_bytes(nb)

    job_manager.set_result(job_id, nb_bytes)
    job_manager.set_status(job_id, JobStatus.COMPLETED)
```

Errors from `extract_text_from_pdf` and `generate_tutorial` are caught as `ValueError` and stored in the job. Auth errors are prefixed with `AUTH:` so the frontend can show a specific message.

### backend/services/pdf_extractor.py
**Purpose**: Extracts text from PDF files using pdfplumber with page markers.
**Key Function**:
- `extract_text_from_pdf(file_bytes: bytes) -> str`

**How it works**:
Opens the PDF from raw bytes using `pdfplumber.open(io.BytesIO(file_bytes))`. Iterates through all pages, extracting text from each and inserting `--- Page N ---` markers between them. After extraction, checks if any actual text was found (ignoring the page markers themselves). If no text is found, raises `ValueError` with a message about scanned/image-based PDFs. This handles the edge case of PDFs that are just scanned images with no OCR layer.

### backend/services/openai_service.py
**Purpose**: Calls GPT-5.4 to analyze paper text and return structured tutorial JSON.
**Key Function**:
- `generate_tutorial(pdf_text: str, api_key: str) -> dict`

**How it works**:
Constructs an OpenAI client with the user's API key and sends a two-message conversation: a system prompt describing the exact JSON schema expected, and a user prompt containing the paper text. The paper text is inserted via `USER_PROMPT_TEMPLATE.replace("{{PAPER_TEXT}}", pdf_text)` — deliberately using `.replace()` instead of `.format()` because research papers frequently contain `{curly braces}` in mathematical notation that would break Python's format strings.

The response is parsed as JSON, with a fallback that strips markdown code fences (`\`\`\`json ... \`\`\``) since GPT sometimes wraps its output. After parsing, all 9 required keys are validated. Three specific OpenAI error types are caught and re-raised as descriptive `ValueError`s: `AuthenticationError`, `RateLimitError`, and generic `APIError`.

### backend/services/notebook_builder.py
**Purpose**: Converts structured tutorial data into a valid Jupyter notebook.
**Key Functions**:
- `build_notebook(tutorial_data: dict) -> nbformat.NotebookNode`
- `notebook_to_bytes(nb: NotebookNode) -> bytes`

**How it works**:
Creates an nbformat v4 notebook and populates it with cells in a fixed order: title+authors (markdown), executive summary (markdown), pip installs (code), mathematical foundations (markdown with LaTeX `$$` blocks), algorithm sections (each with pseudocode markdown, implementation code, and synthetic data code), visualizations (code cells), ablation study (markdown + code), exercises (markdown with hints), and references (markdown list). Each section is conditionally included — if the GPT response omits visualizations, that section is simply skipped.

`notebook_to_bytes()` serializes the notebook to a JSON string via `nbformat.writes()` and encodes it as UTF-8 bytes, ready to be returned as an HTTP response.

### backend/services/job_manager.py
**Purpose**: Thread-safe in-memory job tracker for background conversion tasks.
**Key Class**: `JobManager` with `JobStatus` enum (PENDING, PROCESSING, COMPLETED, FAILED)

**How it works**:
Each job is a dict with `status`, `messages` (list of strings), `result` (notebook bytes or None), and `error` (string or None). All mutations are guarded by a `threading.Lock` since jobs are created in the async request handler but mutated in background threads. `get_job()` returns a shallow copy to prevent callers from accidentally mutating the internal state.

```python
class JobManager:
    def create_job(self) -> str:
        job_id = uuid.uuid4().hex
        with self._lock:
            self._jobs[job_id] = {
                "status": JobStatus.PENDING,
                "messages": [], "result": None, "error": None,
            }
        return job_id
```

### next.config.js
**Purpose**: Proxies frontend `/api/*` requests to the FastAPI backend.

**How it works**:
Uses Next.js `rewrites()` to map `/api/:path*` to `http://localhost:8000/api/:path*`. This means the frontend can call `/api/convert` without knowing the backend's port — in development, Next.js transparently forwards the request. This also avoids CORS issues since the browser sees all requests going to the same origin.

## Data Flow

1. User enters their OpenAI API key → stored in `sessionStorage` (never leaves the browser until step 4)
2. User drags a research paper PDF onto the UploadZone → stored in React state as a `File` object
3. User clicks "Generate Notebook" → `page.tsx` creates a `FormData` with the file + API key
4. `POST /api/convert` sends the form to FastAPI (via Next.js rewrite proxy)
5. FastAPI validates the file is a PDF, creates a job via `JobManager`, returns `job_id`
6. Background thread: `extract_text_from_pdf()` reads all pages with pdfplumber
7. Background thread: `generate_tutorial()` sends extracted text to GPT-5.4, receives structured JSON
8. Background thread: `build_notebook()` converts the JSON into an nbformat v4 notebook
9. Background thread: `notebook_to_bytes()` serializes to UTF-8 JSON bytes, stored in `JobManager`
10. Frontend polls `GET /api/status/{job_id}` every 1 second, displays messages in StatusFeed
11. When status is `"completed"`, DownloadSection appears with two options:
    - "Download .ipynb" → direct link to `GET /api/download/{job_id}`
    - "Open in Google Colab" → creates anonymous GitHub Gist → opens Colab URL

## Test Coverage

- **Frontend Unit (vitest + testing-library)**: 52 tests
  - `theme.test.ts` (10) — CSS variables, dark background, Inter font, color palette
  - `api-key-input.test.tsx` (7) — render, show/hide toggle, value changes
  - `upload-zone.test.tsx` (9) — drag-drop, file selection, PDF-only validation, remove
  - `generate-button.test.tsx` (4) — enabled/disabled, click handler
  - `page.test.tsx` (8) — component composition, sessionStorage persistence, button state
  - `status-feed.test.tsx` (6) — message rendering, order, monospace style, error display
  - `download-section.test.tsx` (6) — visibility, download href, Colab button
  - `ui-polish.test.tsx` (6) — loading states, error messages, responsive classes

- **Backend Unit (pytest)**: 65 tests
  - `test_health.py` (4) — health endpoint, CORS allow/block, content type
  - `test_pdf_extractor.py` (8) — single/multi page extraction, page markers, empty/invalid PDFs, large PDFs
  - `test_openai_service.py` (13) — API key passing, model selection, .replace() not .format(), JSON parsing, markdown fence stripping, missing keys, auth/rate-limit/API errors, prompt template validation
  - `test_notebook_builder.py` (20) — notebook validity, nbformat v4, all 11 sections present, cell types, roundtrip serialization
  - `test_job_manager.py` (9) — job creation, unique IDs, status transitions, messages, errors
  - `test_convert_api.py` (11) — endpoint validation, full lifecycle, auth errors, extraction errors, descriptive messages, 404s

## Security Measures

- **API key handling**: Stored in `sessionStorage` (not `localStorage`), cleared when tab closes. Only transmitted to the backend in the POST body, never logged or persisted server-side.
- **Input validation**: PDF file type checked by extension on upload. `pdfplumber` gracefully handles malformed PDFs with a `ValueError`.
- **CORS**: Backend only allows `http://localhost:3000` origin.
- **No `.format()` on user content**: The OpenAI prompt uses `.replace()` with `{{PAPER_TEXT}}` to prevent injection via curly braces in paper text.
- **Thread safety**: `JobManager` uses `threading.Lock` for all mutations to prevent race conditions.
- **Dependency auditing**: `pip-audit` and `semgrep` run on every task with zero findings.
- **No secrets in code**: API keys are user-provided at runtime; no hardcoded credentials.

## Known Limitations

- **No true SSE**: The PRD specified Server-Sent Events, but the implementation uses polling (`setInterval` every 1s) instead. This works but is less efficient and introduces up to 1 second of latency on status updates.
- **In-memory job storage**: `JobManager` stores everything in a Python dict. Jobs are lost on server restart, and memory grows unboundedly with usage. Not suitable for production without a cleanup mechanism.
- **Single-threaded processing**: Each job runs in a background thread, but there's no thread pool limit. Under heavy load, this could exhaust system resources.
- **No file size validation**: The PRD specifies 50 MB max, but the backend doesn't enforce this. FastAPI will accept any size file.
- **Colab integration requires anonymous Gist creation**: GitHub's API allows anonymous Gist creation, but it may be rate-limited. The fallback is download-only, which works but isn't ideal.
- **No retry on GPT failures**: If GPT-5.4 returns malformed JSON or times out, the job simply fails. No retry mechanism exists.
- **No progress from GPT**: The status messages during the "Analyzing paper with GPT-5.4..." step are static — there's no streaming or incremental progress from the OpenAI API call, which is the slowest step.

## What's Next

Based on the limitations and the PRD's "Out of Scope" section, v2 priorities should be:

1. **True SSE streaming** — Replace polling with Server-Sent Events for real-time status updates. Stream GPT-5.4 responses for incremental progress during the longest step.
2. **File size validation** — Enforce the 50 MB limit on the backend with a clear error message.
3. **Job cleanup** — Add TTL-based expiration to `JobManager` so completed/failed jobs are cleaned up after 1 hour.
4. **ArXiv URL input** — Allow users to paste an ArXiv URL/ID instead of uploading a PDF. Fetch and extract the paper automatically.
5. **Docker deployment** — Containerize both frontend and backend for consistent deployment.
6. **Rate limiting** — Add per-IP rate limiting to prevent abuse of the conversion endpoint.
