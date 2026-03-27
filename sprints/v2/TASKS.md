# Sprint v2 — Tasks

## Status: In Progress

- [x] Task 1: Add file size and MIME type validation to POST /api/convert (P0)
  - Acceptance: Backend rejects files > 50 MB with 413 status and clear error message. Backend rejects non-PDF files by checking magic bytes (`%PDF` header), not just Content-Type. Returns 400 for invalid file types. Tests cover oversized file, non-PDF file, and valid PDF.
  - Files: backend/main.py, backend/tests/test_input_validation.py
  - Completed: 2026-03-27 — Added MAX_FILE_SIZE (50 MB) check returning 413, PDF magic bytes validation returning 400. 7 new tests (2 size, 5 MIME). 72 total backend tests passing. Semgrep clean, pip-audit clean.

- [x] Task 2: Implement PDF text sanitizer to mitigate prompt injection (P0)
  - Acceptance: `sanitize_pdf_text(text)` strips common prompt injection patterns: "ignore previous instructions", "system:", "assistant:", markdown/HTML injection sequences, and excessive whitespace. Sanitizer is called in the convert pipeline before text is sent to GPT-5.4. Tests cover at least 5 injection patterns and verify clean text passes through unchanged.
  - Files: backend/services/text_sanitizer.py, backend/tests/test_text_sanitizer.py, backend/main.py (update pipeline)
  - Completed: 2026-03-27 — Regex-based sanitizer strips 7 injection patterns (role injection, instruction override, you-are-now), HTML/Markdown injection (script, iframe, image), and collapses excessive whitespace. Wired into convert pipeline after text extraction. 17 new tests. 89 total backend tests passing. Semgrep clean, pip-audit clean.

- [x] Task 3: Add TTL-based job cleanup and max job limit to JobManager (P0)
  - Acceptance: Jobs older than 30 minutes are automatically purged. Maximum 100 concurrent jobs enforced — returns 503 when limit reached. Cleanup runs on each `create_job()` call (no background thread needed). Tests verify TTL expiry, max job rejection, and cleanup of completed jobs.
  - Files: backend/services/job_manager.py, backend/tests/test_job_manager.py (update)
  - Completed: 2026-03-27 — Added created_at timestamp, _cleanup_expired() on create_job(), configurable ttl_seconds (default 1800) and max_jobs (default 100). get_job() also checks TTL. create_job() raises ValueError when limit reached, main.py returns 503. 6 new tests (3 TTL, 3 max limit). 95 total backend tests passing. Semgrep clean, pip-audit clean.

- [ ] Task 4: Move API key from form body to X-API-Key request header (P0)
  - Acceptance: `POST /api/convert` reads the OpenAI API key from `X-API-Key` header instead of form body field. Frontend sends key via header. Backend returns 401 if header is missing. Old form field `openai_api_key` is no longer accepted. Tests updated for new header-based flow.
  - Files: backend/main.py, app/page.tsx, backend/tests/test_convert_api.py (update)

- [ ] Task 5: Add rate limiting middleware with slowapi (P0)
  - Acceptance: `POST /api/convert` limited to 5 requests/minute per IP. `GET /api/status/{job_id}` limited to 30/min per IP. `GET /api/download/{job_id}` limited to 10/min per IP. Returns 429 with `Retry-After` header when exceeded. `GET /health` is not rate-limited. Tests verify rate limit enforcement and 429 response.
  - Files: backend/main.py, backend/requirements.txt (add slowapi), backend/tests/test_rate_limiting.py

- [ ] Task 6: Add security headers middleware (P1)
  - Acceptance: All responses include: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Content-Security-Policy: default-src 'self'`. Headers verified in tests on health, status, and download endpoints.
  - Files: backend/main.py, backend/tests/test_security_headers.py

- [ ] Task 7: Tighten CORS configuration (P1)
  - Acceptance: CORS allows only `GET` and `POST` methods (not PUT, DELETE, PATCH). Allowed headers restricted to `Content-Type`, `X-API-Key`, and standard headers. `allow_credentials` is False. Tests verify disallowed methods get proper CORS rejection.
  - Files: backend/main.py, backend/tests/test_cors.py

- [ ] Task 8: Add request logging middleware for security monitoring (P1)
  - Acceptance: All requests logged with: timestamp, method, path, status code, client IP, response time in ms. Logs written to stdout in structured JSON format. API keys and request bodies are NOT logged. Tests verify log output format and that sensitive data is excluded.
  - Files: backend/middleware/request_logger.py, backend/main.py (register middleware), backend/tests/test_request_logger.py

- [ ] Task 9: Add backend integration test suite for security scenarios (P2)
  - Acceptance: End-to-end tests covering: oversized file rejection, prompt injection in PDF text is sanitized, rate limit triggers 429, expired job returns 404, max jobs returns 503, missing API key header returns 401, CORS preflight for disallowed method. All tests pass. Existing tests still pass.
  - Files: backend/tests/test_security_integration.py

- [ ] Task 10: Update frontend error handling for new security responses (P2)
  - Acceptance: Frontend handles 413 (file too large), 429 (rate limited — shows retry message), 503 (server busy). Error messages are user-friendly and specific. Tests verify error message display for each new status code.
  - Files: app/page.tsx, tests/unit/security-errors.test.tsx
