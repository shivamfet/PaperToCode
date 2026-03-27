# Sprint v3 — PRD: Production-Ready (Testing, CI/CD, Docker & Cloud)

## Overview

Make PaperToCode production-ready with comprehensive E2E testing, a CI/CD pipeline that blocks broken merges, Docker containerization, and automated AWS deployment. The app's functionality is frozen from v2 — this sprint is purely about confidence, automation, and shipping.

## Goals

- E2E Playwright tests covering the full user flow (upload PDF, generate, download) with screenshots at each step
- A real quality test that opens a visible browser, lets the user enter their own API key, generates a notebook from "Attention Is All You Need", and validates the output (valid JSON, 8+ sections, valid Python, safety disclaimer)
- GitHub Actions CI pipeline running pytest, Playwright, semgrep, and pip-audit on every push/PR — merge blocked if any check fails
- Docker images for backend (FastAPI) and frontend (Next.js) with docker-compose for local orchestration
- Terraform config for AWS ECS Fargate deployment with auto-deploy CD after tests pass on main

## User Stories

- As a developer, I want E2E tests that exercise the full app flow in a real browser, so I catch integration issues before they reach users
- As a developer, I want CI to block merges when tests or security scans fail, so broken code never ships
- As an operator, I want `docker compose up` to run the entire app locally, so I can test production-like behavior without manual setup
- As an operator, I want merges to main to auto-deploy to AWS, so shipping is zero-effort after code review
- As a stakeholder, I want a real quality test with screenshots proving the app produces a valid, complete notebook from a real paper

## Technical Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    GitHub Actions CI/CD                    │
│                                                           │
│  on push/PR:                                              │
│    ├─ pytest (backend unit + integration)                 │
│    ├─ playwright (E2E browser tests)                      │
│    ├─ semgrep (SAST security scan)                        │
│    └─ pip-audit (dependency vulnerability scan)           │
│                                                           │
│  on merge to main (after CI passes):                      │
│    ├─ docker build & push to ECR                          │
│    └─ terraform apply → ECS Fargate deploy                │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                    Docker Compose (local)                  │
│                                                           │
│  ┌─────────────────────┐  ┌────────────────────────────┐ │
│  │  frontend (Next.js)  │  │  backend (FastAPI/uvicorn) │ │
│  │  Port 3000           │──│  Port 8000                 │ │
│  │  next.config.js      │  │  gunicorn + uvicorn worker │ │
│  │  rewrites → backend  │  │                            │ │
│  └─────────────────────┘  └────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                 AWS ECS Fargate (prod)                     │
│                                                           │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────────┐ │
│  │   ALB    │──▶│  ECS Service  │──▶│  ECR Images      │ │
│  │ :80/:443 │   │  (2 tasks)    │   │  frontend:latest │ │
│  └──────────┘   │  frontend     │   │  backend:latest  │ │
│                  │  backend      │   └──────────────────┘ │
│                  └──────────────┘                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  CloudWatch Logs (structured JSON from v2 logger)    │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Tech Stack Additions

| Tool | Purpose |
|------|---------|
| Playwright | E2E browser testing (Chromium) |
| GitHub Actions | CI/CD pipeline |
| Docker | Container images for frontend + backend |
| docker-compose | Local multi-service orchestration |
| Terraform | AWS infrastructure as code |
| AWS ECS Fargate | Serverless container hosting |
| AWS ECR | Docker image registry |
| AWS ALB | Load balancer + HTTPS termination |
| CloudWatch | Log aggregation |

## Out of Scope

- New features (ArXiv URL input, SSE streaming, etc.) — functionality is frozen from v2
- HTTPS/TLS certificate provisioning (ALB handles termination, cert is manual or ACM)
- Custom domain setup
- Auto-scaling policies (single task per service is sufficient for launch)
- Database or persistent storage (in-memory JobManager is acceptable for v3)
- Monitoring/alerting dashboards (CloudWatch logs are sufficient)
- Load testing / performance benchmarks

## Dependencies

- Sprint v2 complete (all 10 security tasks shipped)
- GitHub repository connected via `gh` CLI
- AWS IAM user `paper2notebookMSD` with: AmazonEC2FullAccess, AmazonECS_FullAccess, AmazonEC2ContainerRegistryFullAccess, ElasticLoadBalancingFullAccess, IAMFullAccess, CloudWatchLogsFullAccess, AmazonS3FullAccess
- AWS credentials available at `/Users/rajat/Desktop/MSD-PRD/aws_cred.md`
- "Attention Is All You Need" PDF at `/Users/rajat/Desktop/MSD-PRD/NIPS-2017-attention-is-all-you-need-Paper (1).pdf`
