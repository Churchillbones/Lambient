# Ambient Transcription App – Multi-Phase Refactoring & Improvement Roadmap

> Last updated: 2025-06-15

This document captures the high-level, multi-phase strategy for transforming the prototype into a production-ready, maintainable system. Each phase is scoped to be incremental, testable, and deliver measurable value without introducing breaking changes downstream.

---

## Phase 0 – Baseline Stabilisation *(✅ complete)*

1. Pin working commit as rollback point.  
2. Document environment setup (`setup.bat`, manual instructions).  
3. Replace external network calls in tests with local stubs.  
4. Add smoke‐test suite + CI placeholder.

**Success criteria**: All existing features run locally without manual patching; tests pass on fresh clone.

---

## Phase 1 – Core Architecture & Dependency Injection *(✅ complete)*

1. Create `src/core` package.  
   • Exception hierarchy  
   • `container.py` – singleton DI container with auto-wiring.  
2. Define interface contracts for:  
   • Transcribers  
   • LLM providers  
   • Configuration service.  
3. Build factory layer:  
   • `TranscriberFactory` (lazy-loads Vosk / Whisper / Azure-Speech)  
   • `LLMProviderFactory` (Azure OpenAI, Ollama, Local).  
4. Implement provider layer (concrete classes for each backend).  
5. Migrate configuration to `pydantic-settings` (`ApplicationSettings`, `AzureSettings`) + `ConfigurationService`.  
6. Wire factories in `core.bootstrap`.  
7. Refactor legacy modules (`asr.transcription`, `llm.llm_integration`, FastAPI routes) to resolve dependencies via DI.

**Success criteria**: All unit tests green; no module has hard dependency on concrete providers.

---

## Phase 2 – Service Decoupling & SDK Migration *(⏳ in progress)*

1. Eliminate direct Azure SDK invocations (token management, etc.); switch to provider pattern.  
2. Remove remaining legacy stubs (`openai.py`, fallback branches).  
3. Consolidate HTTP client logic; share retry / timeout policy.  
4. Add typed request / response models for all external calls.  
5. Increase unit test coverage to ≥ 80 %.  

**Success criteria**: Swappable cloud vs. local providers behind common interface; tests enforce parity.

---

## Phase 3 – Observability, Linting & Continuous Integration

1. Introduce `pyproject.toml` for tooling: Black, Ruff, MyPy.  
2. Configure pre-commit hooks.  
3. Add GitHub Actions pipeline (lint, type-check, tests).  
4. Integrate structured logging (Python `logging` → JSON).  
5. Expose Prometheus‐style metrics endpoint.

**Success criteria**: PRs fail on lint / type errors; basic metrics visible when running locally.

---

## Phase 4 – Packaging & Deployment

1. Dockerise backend & Ollama bridge (multi-stage build).  
2. Publish versioned images to GHCR.  
3. Produce `pip`-installable package for core library (`src/core`).  
4. Add Makefile scripts for common tasks (`make dev`, `make test`, `make docker`).  

**Success criteria**: `docker compose up` delivers full stack; semver tags generate publish artefacts automatically.

---

## Phase 5 – Frontend Modernisation & UX Polish

1. Audit Angular code; migrate shared state to a dedicated store (NgRx / Signals).  
2. Integrate Tailwind CSS for rapid styling.  
3. Add responsive layout & accessibility improvements.  
4. Implement websocket progress updates (recording → transcription → note generation).

**Success criteria**: End-to-end demo on mobile + desktop with live feedback.

---

## Phase 6 – Performance, Security & Compliance

1. Profile hot paths (ASR decoding, LLM calls) ⇒ optimise batching / concurrency.  
2. Enable optional AES-GCM encryption for stored audio + notes.  
3. Add role-based auth & audit logging.  
4. Perform dependency vulnerability scans (Dependabot).

**Success criteria**: P95 latency ≤ target; OWASP top-10 risks mitigated; passing security scan.

---

## Phase 7 – Documentation & Release Engineering

1. Generate API reference from docstrings (mkdocs-material).  
2. Author tutorials & architecture diagrams.  
3. Add CHANGELOG + release workflow (semantic-release).  
4. Publish `v1.0`.  

**Success criteria**: One-click deploy instructions; newcomers can contribute with <30 min onboarding.

---

### Living Document
Amend tactics as realities evolve, but respect phase boundaries to keep iterations focused and deliverable-oriented. 