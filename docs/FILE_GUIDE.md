# CogniSynth File Responsibility Map

| Path | Primary Responsibility |
|---|---|
| `app.py` | Full multi-tab Streamlit dashboard providing overview, dynamic plan inspection, evidence provenance, contradiction debate, publication report, telemetry traces, and persistent memory search. |
| `api.py` | FastAPI application exposing REST management endpoints and Server-Sent Events (SSE) streaming (`/api/research`) with complete backward compatibility. |
| `pipeline.py` | Legacy pipeline adapter exposing `run_research_pipeline_stream` and `run_research_pipeline`, routing directly into `cognisynth.services.research_service`. |
| `agent.py` | Legacy agent definitions adapter exporting `GeminiChatModel`, `AgentRunner`, `DirectSearchRunner`, `writer_chain`, `review_chain`. |
| `tool.py` | Legacy tools adapter exporting `web_search`, `scrape_url`, `extract_main_content`. |
| `test.py` | Automated smoke test verifying legacy runner and scraper functionality. |
| `src/cognisynth/config.py` | Centralized platform configuration, environment variable validation, and safe defaults using Pydantic Settings. |
| `src/cognisynth/logging_config.py` | Structured JSON and console logging with correlation IDs (`run_id`, `task_id`). |
| `src/cognisynth/schemas/research.py` | Pydantic data models for `ResearchRequest`, `ResearchPlan`, `ResearchTask`, and `ResearchRun`. |
| `src/cognisynth/schemas/evidence.py` | Data models for `Source`, `Document`, `Claim`, and `Evidence`. |
| `src/cognisynth/schemas/report.py` | Data models for `Report`, `ReportVersion`, `Conflict`, and `VerificationResult`. |
| `src/cognisynth/schemas/evaluation.py` | Data models for `EvaluationResult` and `BenchmarkCase`. |
| `src/cognisynth/tools/llm.py` | Resilient Google Gemini REST adapter with exponential backoff, jitter, retry logic, and fallback from `gemini-3.8-flash` to `gemini-3.6-flash`. |
| `src/cognisynth/tools/search.py` | Tavily search adapter producing structured `Source` and `Document` records with domain classification. |
| `src/cognisynth/tools/scraper.py` | Readability and BeautifulSoup web extraction tool converting HTML into sanitized `Document` instances. |
| `src/cognisynth/agents/planner.py` | Dynamic research planner converting research queries into directed acyclic task graphs with safeguards. |
| `src/cognisynth/agents/researcher.py` | Subtask search execution agent querying Tavily and scoring discovered sources. |
| `src/cognisynth/agents/scraper.py` | Deep article extraction agent. |
| `src/cognisynth/agents/analyst.py` | Multidisciplinary technical synthesis agent analyzing verified claims and empirical data. |
| `src/cognisynth/agents/verifier.py` | Fact-checking agent verifying claims against evidence, calculating non-fabricated confidence, and detecting contradictions. |
| `src/cognisynth/agents/critic.py` | Adversarial QA review agent auditing reports against 7 quality criteria and debate checks. |
| `src/cognisynth/agents/reporter.py` | Publication reporter synthesizing structured markdown reports with authentic citations. |
| `src/cognisynth/graph/state.py` | Typed LangGraph state definition (`ResearchGraphState`). |
| `src/cognisynth/graph/builder.py` | Compiles the LangGraph state machine with nodes, transitions, and cycle safeguards. |
| `src/cognisynth/graph/router.py` | Dynamic conditional routing for approval gates and verification decisions. |
| `src/cognisynth/evidence/scorer.py` | Evaluates source domain authority, extraction depth, and directness into a composite quality score. |
| `src/cognisynth/evidence/extractor.py` | Extracts atomic propositional claims and links them to verbatim evidence snippets. |
| `src/cognisynth/evidence/conflicts.py` | Identifies opposing claims, polarity disputes, and numerical discrepancies into explicit `Conflict` records. |
| `src/cognisynth/evidence/verifier.py` | Calculates derived confidence from coverage, agreement, and source reliability without fabrication. |
| `src/cognisynth/memory/store.py` | Abstract storage interface. |
| `src/cognisynth/memory/vector_store.py` | Local zero-dependency vector store implementing TF-IDF cosine similarity and JSON disk persistence. |
| `src/cognisynth/memory/repository.py` | Persistent research run and version repository computing report diff summaries. |
| `src/cognisynth/services/research_service.py` | Master research service coordinating dynamic execution, real-time streaming, and persistence. |
| `src/cognisynth/services/approval_service.py` | Human-in-the-loop checkpoint service managing plan and evidence review gates. |
| `src/cognisynth/observability/events.py` | Typed, versioned streaming SSE event contracts. |
| `src/cognisynth/observability/tracing.py` | Microsecond execution span and state transition telemetry tracer. |
| `src/cognisynth/observability/cost.py` | Token accounting and USD cost estimation engine. |
| `src/cognisynth/evaluation/metrics.py` | Calculates citation accuracy, claim grounding, source recall, and unsupported-claim rate. |
| `src/cognisynth/evaluation/benchmark.py` | Offline benchmark test runner evaluating questions against golden criteria. |
| `evals/questions.json` | Benchmark question set covering deep tech, AI benchmarks, hardware, and systems. |
| `evals/expected_outputs.json` | Benchmark target thresholds and scoring rubric. |
| `docs/architecture.md` | In-depth technical architecture, system design decisions, and tradeoffs. |
| `docs/data-model.md` | Field-level specifications for all Pydantic schemas. |
| `docs/evaluation.md` | Evaluation methodology, benchmark results, and reproducibility instructions. |
| `docs/CHANGELOG_UPGRADE.md` | Human-readable upgrade log in mandatory tabular format. |
