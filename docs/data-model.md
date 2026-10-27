# CogniSynth Data Model Specifications

This document outlines the field-level specifications for all Pydantic v2 schemas in `src/cognisynth/schemas/`.

---

## 1. Research Schemas (`schemas/research.py`)

### `ResearchTask`
- `task_id` (str): Unique task identifier (e.g. `task_a1b2c3d4`).
- `type` (TaskType): `search`, `scrape`, `extract_claims`, `verify`, `synthesize`, `critique`.
- `objective` (str): Specific natural language goal or angle.
- `dependencies` (list[str]): List of prerequisite `task_id`s.
- `priority` (int): Execution priority (1 = highest).
- `status` (TaskStatus): `pending`, `running`, `completed`, `failed`, `skipped`.
- `output_refs` (list[str]): Output artifact references.
- `error` (Optional[str]): Error message if execution failed.

### `ResearchPlan`
- `plan_id` (str): Unique plan identifier.
- `objective` (str): Overall user query.
- `tasks` (list[ResearchTask]): Ordered list of DAG tasks.
- `constraints` (dict[str, Any]): Maximum tasks, depth, timeouts.
- `created_at` (datetime): UTC creation timestamp.

### `ResearchRun`
- `run_id` (str): Correlation run ID.
- `query` (str): Initial research topic.
- `status` (RunStatus): `queued`, `planning`, `executing`, `completed`, `failed`.
- `plan_id` (Optional[str]): Associated plan ID.
- `metrics` (dict[str, Any]): Aggregated run metrics (tokens, latency, confidence).
- `final_report_id` (Optional[str]): Link to generated report.

---

## 2. Evidence Schemas (`schemas/evidence.py`)

### `Source`
- `source_id` (str): Unique source ID (e.g. `src_8f12a3`).
- `url` (str): Full web URL.
- `title` (str): Extracted page title.
- `domain` (str): Normalized domain (e.g. `nature.com`).
- `publisher` (Optional[str]): Organization or publisher name.
- `retrieved_at` (datetime): Retrieval timestamp.
- `source_type` (SourceType): `academic`, `government`, `news`, `technical_docs`, `blog`, `general_web`.
- `quality_score` (float): Derived reliability score [0.0 - 1.0].

### `Document`
- `document_id` (str): Unique document ID.
- `source_id` (str): Parent source reference.
- `text` (str): Cleaned readable article body.
- `extraction_method` (str): Parser used (`readability-lxml`).
- `char_count` (int): Text length in characters.

### `Claim`
- `claim_id` (str): Unique claim ID (e.g. `clm_5e3d`).
- `text` (str): Atomic propositional statement of fact or measurement.
- `type` (ClaimType): `factual`, `statistical`, `predictive`, `opinion`.
- `importance` (float): Weight in overall analysis [0.0 - 1.0].
- `status` (ClaimStatus): `unverified`, `verified`, `contested`, `refuted`.
- `evidence_refs` (list[str]): References to supporting `evidence_id`s.
- `confidence` (float): Fact-checking confidence [0.0 - 1.0].

### `Evidence`
- `evidence_id` (str): Unique evidence ID.
- `claim_id` (Optional[str]): Claim linked to this snippet.
- `source_id` (str): Source origin.
- `snippet` (str): Verbatim quoted text excerpt.
- `relevance` (float): Semantic match score [0.0 - 1.0].
- `directness` (float): Direct empirical measurement vs indirect commentary [0.0 - 1.0].

---

## 3. Report Schemas (`schemas/report.py`)

### `Conflict`
- `conflict_id` (str): Unique conflict ID.
- `claim_refs` (list[str]): Contradictory `claim_id`s.
- `explanation` (str): Description of the disagreement.
- `severity` (ConflictSeverity): `low`, `medium`, `high`.
- `resolution` (Optional[str]): Guidance on reconciling the discrepancy.

### `ReportVersion`
- `report_id` (str): Parent report ID.
- `version` (int): Monotonically increasing version number (1, 2, 3...).
- `markdown_content` (str): Full text of report.
- `claims` (list[str]): Included claim IDs.
- `citations` (list[str]): Included source IDs.
- `confidence` (float): Confidence score at time of publication.
- `change_summary` (Optional[str]): Automated diff summary comparing against previous version.
