# PHASE 4: Packaging & Deployment – Implementation Plan

> **Goal** Deliver reproducible, one-command deployment options (Docker & Python package) and automate artefact publishing on semantic version tags.

---

## 0  High-Level Objectives

1. **Containerisation** – multi-stage, minimal-size Docker images for backend, Ollama bridge, and frontend.
2. **Registry Publishing** – versioned images pushed to GHCR & Docker Hub via CI.
3. **Python Distribution** – publish `ambient-gpt-core` (src/core) to PyPI with extras (`asr`, `llm`, `fastapi`).
4. **Local Dev Ergonomics** – Makefile / task runner for dev, test, build, release.
5. **Infrastructure as Code** – Docker Compose for local, Helm chart for Kubernetes.

---

## 1  Detailed Work Packages & Steps

### STEP 4.1  Docker & Compose
* Create `docker/backend/Dockerfile` multi-stage:  
  stage 1: `python:3.11-slim` build deps  
  stage 2: runtime with non-root user, copy wheels & source.
* `docker/ollama-bridge/Dockerfile` – Flask wrapper image.
* Add `docker-compose.yml` with services: `api`, `bridge`, `frontend`, `postgres` (future), `grafana`.
* Implement healthchecks; ensure `docker compose up` works locally.

### STEP 4.2  GitHub Actions – Container Publish
* New workflow `docker.yml` triggered on tag `v*`.
* Build platform matrix (`linux/amd64`, `linux/arm64`) using `docker buildx`.
* Push to `ghcr.io/<org>/ambient-gpt-api` & `ambient-gpt-bridge`.
* Add Docker Hub mirror (optional) – use repo secret `DOCKERHUB_TOKEN`.

### STEP 4.3  PyPI Package
* Split reusable code under `src/core` into standalone distribution `ambient-gpt-core`.
* Add `setup.cfg` with metadata, entry-points (`ambient-gpt = core.cli:app`).
* Build wheels via `build`, publish in `publish-pypi.yml` gated on `pypi` secret.
* Provide extras:  
  `pip install ambient-gpt-core[whisper]` etc.

### STEP 4.4  Helm Chart
* Directory `deploy/chart/ambient-gpt-notes/` with `Chart.yaml`, `values.yaml`, templates.
* Features: Ingress, HPA, secret mounts, persistence for `app_data/`.
* CI step validates chart with `helm lint` and pushes to `gh-pages` branch using `helm/chart-releaser`.

### STEP 4.5  Makefile & Scripts
* `Makefile` commands: `dev`, `test`, `lint`, `docker-build`, `release`.
* Windows-friendly PowerShell equivalents.

### STEP 4.6  Release Automation & SemVer
* Adopt `semantic-release` (Python) or conventional commits parser.
* Tags trigger:  
  1. PyPI wheel upload  
  2. Docker image build/push  
  3. Helm chart release  
  4. GitHub Release notes generation.

---

## 2  Implementation Timeline & Tracking

| Week | Focus                   | Deliverables                              |
|------|-------------------------|-------------------------------------------|
| 1    | Docker & Compose        | Working `docker compose up`               |
| 2    | CI container workflow   | `docker.yml`, images pushed on tag        |
| 3    | PyPI packaging          | Build wheels locally, dry-run upload      |
| 4    | Helm chart & lint       | `helm install` works on kind cluster      |
| 5    | Makefile & SemVer       | `make release` produces all artefacts     |

---

## 3  Quality-Assurance Checklist

- [ ] Backend image ≤ 300 MB, bridge ≤ 150 MB
- [ ] `docker compose up` passes smoke-tests on Windows & Linux
- [ ] `pip install ambient-gpt-core` works on Py 3.9-3.12
- [ ] Helm chart `helm test` green
- [ ] CI publishes artefacts on `v*` tag automatically

---

## 4  Success Criteria

1. **One-command deployment** via Docker Compose and Helm.
2. Versioned images & wheels appear in registries within 5 min of tag.
3. Developers can consume core library via PyPI and extend providers.
4. Image rebuild < 5 min; cold-start < 1 s on 2-CPU micro-VM.

---

> **Next Action** — merge this plan, create Phase 4 board column, open issues per work-package. 