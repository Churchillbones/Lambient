# PHASE 3: Production Readiness & Release Hardening – Implementation Plan

> **Goal** Elevate the application from "internally stable" to a **public-grade release candidate**.  
> Focus on operational excellence, performance, user experience, security, and deployment automation.

---

## 0  High-Level Objectives

1. **CI/CD Hardening** – enforce quality gates on every PR, automated Docker / artefact builds, one-click deploys.
2. **Performance & Scalability** – real-time streaming transcription, batching, GPU acceleration, and async I/O tuning.
3. **Security & Compliance** – threat-model review, OWASP scan, secrets management, encryption-at-rest & in-transit.
4. **Observability** – structured logging, metrics (Prometheus), tracing (OpenTelemetry), uptime / SLA dashboards.
5. **UX Polish** – responsive Tailwind UI, accessibility (WCAG 2.1 AA), on-boarding tour, error surfaces.
6. **Documentation & Examples** – complete MkDocs site, OpenAPI schema, architecture deep-dives, code samples.
7. **Release Packaging** – Docker images, Helm chart, Windows installer, PyPI extras.

---

## 1  Detailed Work Packages & Steps

### STEP 3.1  CI/CD & Release Pipeline
* Create GitHub Actions workflow `release.yml` with:
  * SemVer tagging (PR title triggers `vX.Y.Z`)  
  * Build & push multi-arch Docker images (`linux/amd64`, `linux/arm64`)
  * Publish Helm chart to `gh-pages` branch
  * Publish Python package (`ambient-gpt-notes`) to PyPI on tag
* Integrate Dependabot & CodeQL security analysis.
* Enforce pre-commit + coverage ≥ 90 % in CI gate.

### STEP 3.2  Streaming Transcription
* Implement **WebSocket** endpoint (`/ws/transcribe`) in FastAPI.
* Refactor transcribers to feed partial results (generator / async iterator).
* Frontend: Angular service using `RxJS` WebSocket to stream interim captions.
* Buffer drafts on client, send final transcript for GPT note generation.
* Load-test: ≤ 500 ms latency for 30-sec audio chunks on 8-core box.

### STEP 3.3  Performance Optimisation
* Profiling tasks with `py-spy` & `asyncio` event-loop diagnostics.
* Convert blocking IO (file, FFmpeg) to `asyncio.to_thread`.
* GPU: enable CUDA inference for Whisper (+ torch CUDA wheels) behind feature flag.
* Model warm-pool & caching (LRU) to eliminate cold starts.

### STEP 3.4  Security & Compliance
* Run OWASP dependency-check and bandit high severity rules.
* Secrets: migrate to **Azure Key Vault** / `.env.docker` for containers.
* Add AES-GCM encryption for transcripts stored on disk.
* Draft HIPAA/PII data-flow diagram.

### STEP 3.5  Observability Stack
* Integrate **Structlog** JSON logging with request IDs.
* Expose Prometheus `/metrics` endpoint via `prometheus_fastapi_instrumentator`.
* Use **OpenTelemetry** SDK + Jaeger exporter for distributed traces.
* Grafana dashboard JSON committed under `ops/grafana/`.

### STEP 3.6  Frontend Enhancements
* Convert Angular styling to **Tailwind v4** utility classes.
* Add **Dark Mode** toggle, keyboard shortcuts.
* Internationalisation (i18n) using `ngx-translate`.
* Lighthouse score ≥ 90 (performance / accessibility / best-practices).

### STEP 3.7  Documentation Completion
* MkDocs Material custom theme, version selector.
* Auto-generate OpenAPI docs via `mkdocs-openapi-plugin`.
* Example notebooks (`docs/examples/*.ipynb`) for Python SDK usage.
* Architecture ADRs under `docs/adr/` (event sourcing, provider pattern, etc.).

### STEP 3.8  Release Artifacts
* **Docker Hub** repository `ambient/gpt-notes` with tags `latest`, `vX.Y.Z`.
* **Helm Chart** `ambient-gpt-notes` for Kubernetes.
* **Windows MSI** created with `PyInstaller + Wix` (optional).
* Publish tutorial video & blog post.

---

## 2  Implementation Timeline & Tracking

| Week | Focus                                   | Deliverables                                    |
|------|-----------------------------------------|-------------------------------------------------|
| 1    | CI/CD Hardening                         | `release.yml`, Docker push, PyPI dry-run        |
| 2    | Streaming Transcription (backend)       | WebSocket endpoint, transcriber streaming       |
| 3    | Streaming Transcription (frontend)      | Live captions in UI, load-test metrics          |
| 4    | Performance Optimisation                | Benchmarks, GPU flag, cold-start < 1 s          |
| 5    | Security, Observability                 | Key Vault integration, Prometheus & traces      |
| 6    | UX Polish & Docs                        | Tailwind UI, Lighthouse ≥ 90, docs complete     |
| 7    | Release Packaging                       | Helm chart, Docker Hub, MSI, announcement post  |

*(Timeline assumes 6-7 hrs/week developer bandwidth.)*

---

## 3  Quality-Assurance Checklist

- [ ] Coverage ≥ 90 % (backend src + utils)
- [ ] Docker image < 800 MB, cold-start < 1 s
- [ ] p95 streaming latency < 500 ms for 30-sec audio
- [ ] CI passes on Py 3.9-3.12, Windows & Linux
- [ ] OWASP/ZAP scan shows no critical issues
- [ ] Lighthouse accessibility ≥ 90
- [ ] All ADRs & docs build without warnings (`mkdocs build`)

---

## 4  Success Criteria

1. Users can transcribe + generate notes **in real-time** with < 0.5 s lag.
2. Single-command deployment to Kubernetes or Docker Compose.
3. Metrics & traces visible in Grafana within 1 min of start-up.
4. No P1 security findings in CodeQL or OWASP-Zap scans.
5. Positive UX score from pilot clinicians; no blocker feedback.

---

### Change-Log Section (fill as we progress)

| Date | Commit / PR | Work-Package | Notes |
|------|-------------|--------------|-------|
| —    | —           | —            | Plan drafted |

---

> **Next Action** — merge this plan, create Phase 3 column on the project board, seed issues per work-package. 