# PHASE 2: Legacy Elimination & Service Abstraction – Implementation Plan

> **Goal**  Finish the migration from proof-of-concept to production-ready code by eradicating
> remaining legacy SDK calls, completing provider abstraction, tightening quality gates,
> and expanding test coverage.  
> This builds on Phase 1's DI & factory foundation.

---

## 0  High-Level Objectives

1. **Provider-First Architecture**  – absolutely *no* business code should import an SDK
   directly (Azure, Whisper, etc.). Everything routes through a provider registered in the
   DI container.
2. **Platform Flexibility**  – token-management & ASR utilities must be provider-agnostic so
   cloud, local, or future vendors are drop-in.
3. **Operational Excellence**  – add pre-commit hooks, coverage checks, multi-version CI,
   and `docs/` skeleton.
4. **Cleanup**  – remove temporary stubs (`dotenv.py`, `requests.py`, etc.) and dead code.

---

## 1  Detailed Work Packages & Steps

### STEP 2.1  LLM Provider Roll-Out (Codebase-Wide)
**Files Touched:** `src/llm/*.py`, `src/asr/**.py`, tests

1. **Audit**: grep for `AzureOpenAI(`, `AsyncAzureOpenAI(`, `requests.post(`/generate_note`, etc.).
2. **Create Adapter Helpers** (if needed) in `core/providers/` for:
   • OpenAI chat completions (non-Azure)
   • Any other hard-coded local APIs.
3. **Refactor** each call-site to:
   ```python
   provider = container.resolve(LLMProviderFactory).create("azure_openai", **ctx)
   content = await provider.generate_completion(prompt)
   ```
4. **Unit tests** for new integration paths using dummy provider.

### STEP 2.2  Token-Management Service
**New:** `src/core/services/token_service.py`

1. Define `ITokenService` interface (count, chunk, summarise).  
2. Move logic from `src/llm/token_management.py` → concrete `OpenAITokenService` & keep
   fallback for non-tiktoken installs.
3. Register singleton in container; update callers.
4. Tests for chunking edge-cases.

### STEP 2.3  ASR Provider Completion

1. Implement `AzureSpeechTranscriber` provider in `core/providers/` conforming to
   `ITranscriber`.
2. Extend `TranscriberFactory` default map.
3. Remove legacy `src/asr/azure_speech.py` direct SDK usages.
4. Verify Vosk/Whisper providers already match interface; if not, wrap.

### STEP 2.4  Stub Removal & Real Package Adoption

1. Delete `dotenv.py`, `requests.py`, `bleach.py`, `pyaudio.py` stubs.
2. Add missing libraries behind optional imports or extras.
3. Update tests to use `pytest-mock` to patch external calls where needed.

### STEP 2.5  Tooling & CI Enhancements

1. **Pre-commit**: add `.pre-commit-config.yaml` running Ruff, Black, and `pytest --quiet`.
2. **CI**: extend matrix to {3.9, 3.10, 3.11}; add coverage job (pytest-cov + Codecov).
3. **Ruff**: enable additional rule sets (`D` docstrings, `PL` pylint-port).
4. **Sphinx / MkDocs**: scaffold under `docs/` for later detailed docs.

### STEP 2.6  Documentation & Examples

1. Update `README.md` with architecture diagram & provider usage examples.
2. Draft `docs/usage/` pages for common CLI & API flows.

---

## 2  Implementation Timeline & Tracking

| Week | Focus                                  | Deliverables |
|------|----------------------------------------|--------------|
| 1    | LLM Provider Roll-Out                  | Codebase free of direct SDK calls; green tests |
| 2    | Token Service Extraction               | `ITokenService`, provider impl, tests |
| 3    | ASR Provider Completion                | AzureSpeech provider; factories updated |
| 4    | Stub Removal & Cleanup                 | All temp stubs deleted; CI green |
| 5    | Tooling & CI Enhancements              | Pre-commit, coverage, multi-version matrix |
| 6    | Docs & Wrap-Up                         | Updated README, docs skeleton, hand-off report |

*(Timeline assumes ~1 week iteration; adjust per capacity.)*

---

## 3  Quality-Assurance Checklist

- [ ] All direct SDK imports eliminated from app layer
- [ ] 100 % provider construction via DI container
- [ ] Unit-test coverage ≥ 90 % for new core services
- [ ] CI passing on Python 3.9–3.11
- [ ] Ruff + Black pre-commit passes locally & in CI
- [ ] No stub modules remain in repository root
- [ ] Updated docs build without warnings (`mkdocs build`)

---

## 4  Success Criteria

1. Application runs end-to-end with either Azure or local (Ollama) back-ends by *only*
   swapping configuration – zero code changes.
2. Developers can mock any provider via the DI container in tests.
3. Build pipeline gates (lint, format, tests, coverage) must pass before merge.
4. Comprehensive plan & checklists (this file) kept in sync until Phase 2 is marked ✅.

---

### Change-Log Section (fill as we progress)

| Date | Commit / PR | Work-Package | Notes |
|------|-------------|--------------|-------|
| —    | —           | —            | Plan drafted |

---

> **Next Action**  — Merge this plan to `main`; create GitHub Project board with
> "Phase 2" column mirroring the work packages above. 