# CogniSynth Upgrade Changelog

## PHASE 0 — Foundation & Architecture
| File | Change | Reason | Tests |
|---|---|---|---|
| `src/cognisynth/config.py` | Centralized Pydantic Settings and environment validation | Eliminate hardcoded configs and enforce key checks | `tests/unit/test_schemas.py` |
| `src/cognisynth/logging_config.py` | Added structured JSON logging and correlation IDs | Auditable run traces | `tests/unit/test_schemas.py` |
| `src/cognisynth/schemas/research.py` | Added ResearchRequest, ResearchPlan, ResearchTask, ResearchRun | Typed research execution state | `tests/unit/test_schemas.py` |
| `src/cognisynth/schemas/evidence.py` | Added Source, Document, Claim, Evidence | Structured evidence provenance | `tests/unit/test_schemas.py` |
| `src/cognisynth/schemas/report.py` | Added Conflict, VerificationResult, ReportVersion, Report | Auditable reporting contracts | `tests/unit/test_schemas.py` |
| `src/cognisynth/schemas/evaluation.py` | Added EvaluationResult, BenchmarkCase | Reproducible benchmarks | `tests/unit/test_schemas.py` |
| `src/cognisynth/tools/llm.py` | Preserved GeminiChatModel with backoff, jitter, and fallback | Zero-downtime resilience | `tests/unit/test_schemas.py` |
| `src/cognisynth/tools/scraper.py` | Added clean Readability/BS4 extractor returning Document | Safe, bounded web scraping | `tests/unit/test_schemas.py` |
| `src/cognisynth/tools/search.py` | Added structured Tavily search returning Source/Document pairs | Clean web ingestion | `tests/unit/test_schemas.py` |

## PHASE 1 — Dynamic Planning
| File | Change | Reason | Tests |
|---|---|---|---|
| `src/cognisynth/agents/planner.py` | Implemented dynamic PlannerAgent for DAG task decomposition | Replace rigid fixed flow | `tests/unit/test_planner.py` |
| `src/cognisynth/graph/state.py` | Defined typed LangGraph ResearchGraphState | State preservation across nodes | `tests/unit/test_planner.py` |
| `src/cognisynth/graph/builder.py` | Constructed dynamic multi-agent LangGraph workflow | State machine orchestration | `tests/unit/test_planner.py` |
| `src/cognisynth/graph/router.py` | Added dynamic conditional routing & safeguard exits | Prevent infinite loops | `tests/unit/test_planner.py` |

## PHASE 2 — Evidence Intelligence
| File | Change | Reason | Tests |
|---|---|---|---|
| `src/cognisynth/evidence/scorer.py` | Added domain authority, extraction, and quality scoring | Filter low-quality sources | `tests/unit/test_source_scoring.py` |
| `src/cognisynth/evidence/extractor.py` | Implemented atomic claim & verbatim snippet extraction | Ground all report statements | `tests/unit/test_evidence.py` |
| `src/cognisynth/agents/researcher.py` | Built ResearcherAgent executing subtasks | Target specific query angles | `tests/unit/test_source_scoring.py` |
| `src/cognisynth/agents/scraper.py` | Built ScraperAgent for full-article extraction | Deep document ingestion | `tests/unit/test_evidence.py` |

## PHASE 3 — Verification & Reasoning
| File | Change | Reason | Tests |
|---|---|---|---|
| `src/cognisynth/evidence/conflicts.py` | Added contradiction detector for polarity and numbers | Explicit conflict tracking | `tests/unit/test_conflicts.py` |
| `src/cognisynth/evidence/verifier.py` | Implemented non-fabricated derived confidence engine | Derived confidence from signals | `tests/unit/test_evidence.py` |
| `src/cognisynth/agents/verifier.py` | Built VerifierAgent orchestrating claims & conflicts | Fact-checking audit | `tests/unit/test_conflicts.py` |
| `src/cognisynth/agents/analyst.py` | Built AnalystAgent for thematic multi-source synthesis | High-depth reasoning | `tests/integration/test_pipeline_stream.py` |
| `src/cognisynth/agents/critic.py` | Built CriticAgent for adversarial debate and QA audit | Rigorous 7-point review | `tests/integration/test_pipeline_stream.py` |
| `src/cognisynth/agents/reporter.py` | Built ReporterAgent for citation-grounded reports | Final report generation | `tests/integration/test_pipeline_stream.py` |

## PHASE 4 — Persistent Research
| File | Change | Reason | Tests |
|---|---|---|---|
| `src/cognisynth/memory/vector_store.py` | Created LocalVectorStore with cosine similarity | Zero-dependency local semantic retrieval | `tests/unit/test_vector_store.py` |
| `src/cognisynth/memory/repository.py` | Created ResearchRepository with report version diffing | Track report changes over time | `tests/unit/test_vector_store.py` |
| `src/cognisynth/memory/store.py` | Defined abstract storage interfaces | Pluggable persistence layer | `tests/unit/test_vector_store.py` |

## PHASE 5 — Human-in-the-Loop
| File | Change | Reason | Tests |
|---|---|---|---|
| `src/cognisynth/services/approval_service.py` | Implemented ApprovalService and audit checkpoints | Plan/evidence review gates | `tests/integration/test_pipeline_stream.py` |

## PHASE 6 — Observability
| File | Change | Reason | Tests |
|---|---|---|---|
| `src/cognisynth/observability/events.py` | Added typed, versioned SSE event serializers | Rich real-time frontend data | `tests/integration/test_pipeline_stream.py` |
| `src/cognisynth/observability/tracing.py` | Added RunTracer and ExecutionSpan timing | Microsecond latency visibility | `tests/integration/test_pipeline_stream.py` |
| `src/cognisynth/observability/cost.py` | Added CostTracker estimating USD per Gemini tier | Real-time budget monitoring | `tests/integration/test_pipeline_stream.py` |

## PHASE 7 — Evaluation
| File | Change | Reason | Tests |
|---|---|---|---|
| `evals/questions.json` | Added 4 comprehensive benchmark research queries | Standardized evaluation set | `tests/evaluation/test_benchmark.py` |
| `evals/expected_outputs.json` | Defined target thresholds for grounding and recall | Objective quality bar | `tests/evaluation/test_benchmark.py` |
| `src/cognisynth/evaluation/metrics.py` | Implemented automated metrics calculation | Reproducible evaluation score | `tests/evaluation/test_benchmark.py` |
| `src/cognisynth/evaluation/benchmark.py` | Built automated offline benchmark runner | CI/CD evaluation runner | `tests/evaluation/test_benchmark.py` |

## PHASE 8 — Productization
| File | Change | Reason | Tests |
|---|---|---|---|
| `app.py` | Upgraded to multi-view dark dashboard with 7 tabs | Production UI experience | Manual / Browser |
| `api.py` | Extended FastAPI with health, runs, semantic, approval | Complete REST API | `tests/integration/test_pipeline_stream.py` |
| `pipeline.py` | Re-exported streaming service with backward compatibility | Legacy API compatibility | `test.py` |
| `agent.py` | Re-exported chains and runners with backward compatibility | Legacy smoke test compatibility | `test.py` |
| `tool.py` | Re-exported scraping/search with backward compatibility | Legacy tools compatibility | `test.py` |

---

### Migration Summary
- **Files added**:
  - `src/cognisynth/__init__.py`, `config.py`, `logging_config.py`
  - `src/cognisynth/schemas/research.py`, `evidence.py`, `report.py`, `evaluation.py`, `__init__.py`
  - `src/cognisynth/tools/llm.py`, `scraper.py`, `search.py`, `__init__.py`
  - `src/cognisynth/agents/planner.py`, `researcher.py`, `scraper.py`, `analyst.py`, `verifier.py`, `critic.py`, `reporter.py`, `__init__.py`
  - `src/cognisynth/graph/state.py`, `builder.py`, `router.py`, `__init__.py`
  - `src/cognisynth/evidence/scorer.py`, `extractor.py`, `conflicts.py`, `verifier.py`, `__init__.py`
  - `src/cognisynth/memory/store.py`, `vector_store.py`, `repository.py`, `__init__.py`
  - `src/cognisynth/services/research_service.py`, `approval_service.py`, `__init__.py`
  - `src/cognisynth/observability/cost.py`, `tracing.py`, `events.py`, `__init__.py`
  - `src/cognisynth/evaluation/metrics.py`, `benchmark.py`, `__init__.py`
  - `evals/questions.json`, `evals/expected_outputs.json`
  - `tests/unit/test_schemas.py`, `test_planner.py`, `test_source_scoring.py`, `test_evidence.py`, `test_conflicts.py`, `test_vector_store.py`
  - `tests/integration/test_pipeline_stream.py`
  - `tests/evaluation/test_benchmark.py`
  - `docs/architecture.md`, `docs/data-model.md`, `docs/evaluation.md`, `docs/FILE_GUIDE.md`, `docs/CHANGELOG_UPGRADE.md`
  - `Dockerfile`, `docker-compose.yml`, `.env.example`
- **Files modified**: `app.py`, `api.py`, `pipeline.py`, `agent.py`, `tool.py`, `README.md`
- **Files deleted**: None
- **Dependencies added**: None (pure zero-dependency architecture utilizing existing virtualenv packages)
- **Environment variables added**: `DATA_DIR`, `LOG_LEVEL`, `ENABLE_HUMAN_APPROVAL`, `REQUEST_TIMEOUT`
- **API endpoints added/changed**:
  - `GET /api/health` [NEW]
  - `GET /api/runs` [NEW]
  - `GET /api/runs/{run_id}` [NEW]
  - `POST /api/search/semantic` [NEW]
  - `GET /api/benchmark` [NEW]
  - `POST /api/approvals/{checkpoint_id}` [NEW]
  - `GET /api/research` [PRESERVED - 100% Backward Compatible]
- **Vector store migrations**: Initialized local JSON vector store in `data/vector_store.json`
- **Known limitations**: Tavily free tier max results limit is 4; Gemini free tier request rate limit is 20 RPM (handled automatically via exponential backoff and `gemini-3.6-flash` fallback).
