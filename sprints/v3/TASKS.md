# Sprint v3 — Tasks

## Status: Not Started

### Testing

- [x] Task 1: Setup Playwright and E2E test infrastructure (P0)
  - Acceptance: Playwright installed with Chromium. `playwright.config.ts` configured with baseURL `http://localhost:3000`, screenshot-on-failure, and a `webServer` config that starts both backend and frontend. A smoke test that loads the homepage and verifies the title passes. `npm run test:e2e` script added to package.json.
  - Files: package.json, playwright.config.ts, e2e/smoke.spec.ts
  - Completed: 2026-03-27 — Playwright 1.58.2 + Chromium installed. Config with webServer for both backend (port 8000) and frontend (port 3000). 2 smoke tests (homepage elements + backend health). `test:e2e` and `test:quality` scripts added. Semgrep clean, pip-audit clean.

- [x] Task 2: E2E Playwright tests — full user flow with screenshots (P0)
  - Acceptance: Test exercises the complete flow: enter API key (mocked backend), upload PDF, click Generate, see status messages in StatusFeed, see DownloadSection appear. Screenshots captured at each step (key entered, file uploaded, generating, complete). Tests run headless in CI, produce screenshot artifacts. Covers error paths: missing API key, invalid file type.
  - Files: e2e/generate-flow.spec.ts, e2e/fixtures/ (test PDF)
  - Completed: 2026-03-27 — 5 E2E tests covering happy path (full flow with 6 screenshots) and error paths (missing API key, invalid file, 401, 429). 10 screenshots total. Mocked backend via Playwright route interception.

- [x] Task 3: Real quality test — visible browser, real API call, notebook validation (P0)
  - Acceptance: A Playwright test that runs in **headed** mode (visible browser). Opens the app, pauses with a dialog prompting the user to enter their OpenAI API key, uploads "Attention Is All You Need" PDF from disk, clicks Generate, waits for completion (up to 5 minutes timeout). After download: validates notebook is valid JSON, has 8+ sections (cells), contains valid Python code cells, includes a safety/disclaimer cell. Screenshots saved at each step as proof. Test is run manually via `npm run test:quality` (not in CI).
  - Files: e2e/quality.spec.ts, package.json (add test:quality script)
  - Completed: 2026-03-27 — Quality test with headed browser, user prompt for API key, real PDF upload, 5-minute timeout, notebook validation (JSON, 8+ cells, code cells, disclaimer). 7 screenshots. PDF path configurable via QUALITY_TEST_PDF env var. test:e2e updated to exclude quality test.

### CI/CD Pipeline

- [x] Task 4: GitHub Actions CI pipeline (P0)
  - Acceptance: `.github/workflows/ci.yml` runs on every push and PR to main. Jobs: (1) backend-tests: install Python deps, run `pytest` (2) frontend-tests: install Node deps, run Playwright E2E in headless mode (3) security-scan: run `semgrep --config auto` on backend/ (4) dependency-audit: run `pip-audit` on requirements.txt. All jobs must pass for PR merge (branch protection rule documented). Jobs run in parallel where possible.
  - Files: .github/workflows/ci.yml
  - Completed: 2026-03-27 — CI workflow with 4 parallel jobs: backend-tests (pytest), frontend-tests (Playwright E2E), security-scan (semgrep), dependency-audit (pip-audit). Triggers on push/PR to main. Validated with 6 unit tests.

- [ ] Task 5: Connect repo to GitHub and verify CI (P0)
  - Acceptance: Repo pushed to GitHub via `gh` CLI. CI workflow triggers on push. All 4 jobs (pytest, playwright, semgrep, pip-audit) pass green. Branch protection rule set on main requiring CI to pass before merge.
  - Files: (no new files — CLI operations only)

### Docker

- [ ] Task 6: Backend Dockerfile (P0)
  - Acceptance: Multi-stage Dockerfile for FastAPI backend. Stage 1: install Python deps. Stage 2: copy app code, expose port 8000, run with gunicorn + uvicorn workers. Image builds successfully, `docker run` serves `/health` endpoint. No secrets baked into the image. `.dockerignore` excludes venv, __pycache__, tests.
  - Files: backend/Dockerfile, backend/.dockerignore

- [ ] Task 7: Frontend Dockerfile (P0)
  - Acceptance: Multi-stage Dockerfile for Next.js frontend. Stage 1: install deps + build (`next build` with standalone output). Stage 2: copy standalone output, expose port 3000, run with `node server.js`. `NEXT_PUBLIC_API_URL` configurable via env var for backend URL. Image builds and serves the app. `.dockerignore` excludes node_modules, .next.
  - Files: Dockerfile (project root), .dockerignore

- [ ] Task 8: docker-compose.yml for local orchestration (P0)
  - Acceptance: `docker compose up` starts both frontend and backend. Frontend proxies API requests to backend service. Health check on backend `/health`. Services share a Docker network. Ports exposed: 3000 (frontend), 8000 (backend). `docker compose up --build` rebuilds images. README section documents usage.
  - Files: docker-compose.yml

### Cloud Deployment

- [ ] Task 9: Terraform config for AWS ECS Fargate (P1)
  - Acceptance: Terraform creates: VPC with public subnets, ECR repositories (frontend + backend), ECS cluster, ECS task definitions (Fargate), ECS services, ALB with target groups routing `/api/*` to backend and `/*` to frontend, CloudWatch log groups, IAM execution roles. `terraform plan` succeeds with valid config. State stored in S3 bucket. Variables for region, image tags, and environment.
  - Files: infra/main.tf, infra/variables.tf, infra/outputs.tf, infra/providers.tf

- [ ] Task 10: CD pipeline — auto-deploy to AWS on merge to main (P1)
  - Acceptance: `.github/workflows/deploy.yml` triggers on push to main (after CI passes). Steps: build Docker images, push to ECR, run `terraform apply -auto-approve` to update ECS services. AWS credentials stored as GitHub secrets (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY). Deployment only runs if CI workflow succeeds. Output includes the ALB DNS URL.
  - Files: .github/workflows/deploy.yml

### Minimal Additional Tests

- [ ] Task 11: Minimal unit test additions for untested backend paths (P2)
  - Acceptance: Add tests for any untested error paths in pdf_extractor (corrupt PDF, password-protected PDF), notebook_builder (missing optional fields), and job_manager (concurrent access). Target: 5-10 new tests. All existing tests still pass.
  - Files: backend/tests/test_pdf_extractor.py, backend/tests/test_notebook_builder.py, backend/tests/test_job_manager.py
