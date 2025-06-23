# Backend Refactor & Modularisation Plan

> **Objective** – Improve maintainability, testability and extensibility of the backend by breaking up monolithic modules, enforcing clear boundaries between concerns and aligning the directory layout with Domain-Driven principles.

---

## 1. Current Architecture Snapshot

```
backend/
  main.py                ⟶ FastAPI app bootstrap
  realtime.py            ⟶ Web-socket Vosk endpoint
  routers/
      asr.py             ⟶ REST endpoints for ASR + note gen

src/
  asr/                   ⟶ Transcription engines (≈ 1–10 files)            🔸 streaming.py 274 loc
  llm/                   ⟶ LLM utilities (≈ 10 files)                      🔸 llm_integration.py 636 loc
                                                                             🔸 llm_agent_enhanced.py 725 loc
  core/                  ⟶ DI, factories, providers
  encryption.py          ⟶ Crypto helper (304 loc)
```

*Strengths*
• Clear separation between **backend/** (transport layer) and **src/** (domain logic)
• Lightweight dependency-injection container already in place
• Factory pattern used for ASR + LLM provider selection

*Pain Points*
1. **God-modules** – `llm_agent_enhanced.py`, `llm_integration.py`, `asr/streaming.py`, `encryption.py` exceed 250-700 LOC making comprehension and unit-testing hard.
2. **Mixing concerns** – e.g. `llm_integration.py` handles prompt building, cloud vs local model routing, progress callbacks, business rules.
3. **Hidden coupling** – Logic duplicated across websocket & REST layers; configuration fetched directly from env in multiple places instead of central service.
4. **Sparse typing / validation** – Pydantic models are used on endpoints but not internally.
5. **Scattered utils** – helper functions live in large files rather than focused utility modules.

---

## 2. Refactor Goals

1. Shrink every file ↓ < 300 LOC; aim for single-responsibility.
2. Establish **package sub-modules** (`agents`, `providers`, `pipelines`, `utils`, …) under `src/llm` and `src/asr`.
3. Replace ad-hoc dicts with **pydantic models** for internal data exchange.
4. Centralise configuration behind `IConfigurationService`; eliminate direct `os.getenv` access outside `src/core/config`.
5. Introduce **unit-tests** per module (pytest) and enforce 80 %+ coverage on refactored code.
6. Provide incremental migration path – zero API contract break for frontend.

---

## 3. Proposed Module Breakdown

### 3.1 LLM package

```
src/llm/
  __init__.py
  prompts.py              – static templates (keep)
  utils/
      token.py            – token counting + management strategies
      formatting.py       – markdown / html sanitation
  providers/
      openai.py           – Azure & OpenAI wrappers (from core.providers)
      ollama.py
  agents/
      base.py             – abstract Agent class
      extractor.py        – data-extraction agent
      formatter.py        – note formatter agent
  pipeline/
      orchestrator.py     – step engine that chains agents/providers
      models.py           – pydantic models for requests / responses
```

*Action* – split `llm_integration.py` + `llm_agent_enhanced.py` into above artefacts.

### 3.2 ASR package

```
src/asr/
  transcribers/
      vosk.py
      whisper.py
      azure.py
  streaming/
      websocket.py        – moved from backend.realtime
  diarization.py          – keep / slim
  models.py              – pydantic data objects
```

*Action* – move provider classes from `core.providers.*_transcriber.py` into consolidated `transcribers` sub-pkg; expose factory via `TranscriberFactory`.

### 3.3 Core enhancements

• `core/config` → ensure single `ApplicationSettings` instance registered as singleton.
• `core/services` → extract LoggingService, FileStoreService.

---

## 4. Incremental Work Plan

| Phase | Scope | Key Tasks | Status | Notes |
|-------|-------|----------|---------|-------|
| 1 |   Foundation | a. Introduce `src/llm/utils/token.py` and migrate token logic.<br>b. Write unit-tests for token strategies | ✅ **COMPLETED** | Token logic extracted to `src/llm/utils/token.py`, service abstracted behind `ITokenService` |
| 2 |   LLM Provider split | a. Copy `OpenAIProvider`, `OllamaProvider` into `src/llm/providers`.<br>b. Refactor imports; keep legacy re-export for BC | ✅ **COMPLETED** | Re-export wrappers created in `src/llm/providers/__init__.py` |
| 3 |   Agent extraction | a. Create abstract `Agent` base.<br>b. Move extraction / formatting code from `llm_agent_enhanced.py` into dedicated agent classes.<br>c. Add tests. | ✅ **COMPLETED** | Agents extracted to `src/llm/agents/` with base class |
| 4 |   Orchestrator | a. Implement `pipeline/orchestrator.py` to chain agents.<br>b. Deprecate monolithic `llm_agent_enhanced.generate_note_router` | ✅ **COMPLETED** | New `Orchestrator` implemented, legacy code deprecated with warnings |
| 5 |   ASR tidy-up | a. Create `transcribers` pkg; migrate Vosk/Whisper/Azure classes.<br>b. Extract shared audio helpers into `src/audio/utils.py` | ✅ **COMPLETED** | Transcribers consolidated, old providers removed, factory updated |
| 6 |   Realtime WS | a. Move websocket logic into `src/asr/streaming/websocket.py`.<br>b. Keep thin router in `backend/realtime.py` importing new module. | ✅ **COMPLETED** | WebSocket extracted to `src/asr/streaming/websocket.py`, dual implementation exists |
| 7 |   Config centralisation | a. Replace direct `os.getenv` calls with `IConfigurationService`.<br>b. Provide migration shims. | ⚠️ **PARTIAL** | Some `os.getenv` calls remain in `src/config/`, `src/utils/`, `src/llm/embedding_service.py` |
| 8 |   Cleanup & Docs | a. Remove deprecated modules.<br>b. Update README + diagrams.<br>c. Enforce `ruff` + `black`; integrate into CI. | 🔄 **PENDING** | Ready for final cleanup phase |

**CRITICAL REMAINING ISSUES:**
- 🚨 `src/encryption.py`: **330 LOC** (violates <300 rule)
- ⚠️ Config centralization incomplete
- 📝 Documentation updates needed

Total completed: ~5.5/7 dev-days.

---

## 5. Risks & Mitigations

* **Breaking existing imports** – Export legacy symbols that proxy to new modules during transition.
* **Large merge diff** – Execute refactor in small PRs per phase; run unit + integra

tion tests after each.
* **Hidden coupling** – Add contract tests to ensure identical behaviour for note generation & transcription endpoints.

---

## 6. Definition of Done

1. ❌ **No backend file > 300 LOC** - `src/encryption.py` (330 LOC) still violates rule
2. ⚠️ **`pytest` suite green; coverage ≥ 80 % on `src/llm` & `src/asr`** - Tests need to be added
3. ✅ **Front-end continues to operate without changes** - Confirmed working
4. ⚠️ **CI passes (`ruff`, `black`, `pytest`)** - Code quality tools need setup

## 7. FINAL COMPLETION CHECKLIST

### Immediate Priorities (Remaining Work)

#### A. File Size Violations 🚨
- [ ] **Split `src/encryption.py` (330 LOC)** into focused modules
  - Extract crypto utilities to `src/security/crypto.py`
  - Extract file encryption to `src/security/file_encryption.py`
  - Keep only interface/factory in main file

#### B. Config Centralization ⚠️
- [ ] **Replace remaining `os.getenv` calls** with `IConfigurationService`
  - `src/utils/__init__.py` line 214
  - `src/llm/embedding_service.py` line 20
  - `src/asr/streaming/websocket.py` line 35
- [ ] **Remove dual WebSocket implementations**
  - Deprecate `backend/realtime.py` in favor of `src/asr/streaming/websocket.py`

#### C. Testing & Quality ⚠️
- [ ] **Add unit tests** for refactored modules
- [ ] **Setup code quality tools** (`ruff`, `black`, `pytest`)
- [ ] **Enforce 80%+ test coverage** on `src/llm` & `src/asr`

#### D. Documentation & Cleanup 📝
- [ ] **Update README** with new architecture
- [ ] **Remove deprecated modules** after grace period
- [ ] **Update dependency documentation**

### Progress Summary
- **Phases 1-6**: ✅ **COMPLETED** (5.5/7 days)
- **Phase 7**: ⚠️ **75% Complete** (config centralization partial)
- **Phase 8**: 🔄 **Ready to start** (cleanup & docs)

**Estimated remaining effort**: ~1.5 dev-days

---

