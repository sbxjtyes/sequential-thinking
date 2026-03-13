# Changelog

## Version 0.7.5 (2026-03-13) — Claude-Inspired Extended Thinking

### Fixed
- **config.py**: Only merge YAML values when they are dicts; prevents TypeError when `extendedThinking: false` (boolean) is used.
- **reflection.py**: `revises_thought_id` comparison is now case-insensitive (UUIDs).
- **analysis.py**: `generate_summary` conclusions separator uses `"; "` for English, `"；"` for Chinese.
- **advanced_analysis.py**: Removed unused `numpy` import.
- **reflection.py**: Removed redundant `branchExplorationCount` from `extendedThinkingMetrics` (use `reasoningHealth.branchCount`).
- **server.py**: Replaced `json.JSONDecodeError` with `pydantic.ValidationError` for ThoughtData validation failures.

### Added
- **Claude-inspired thought types** (models.py): `self_check` (double/triple-check before concluding), `angle_exploration` (explore different angles and branches of reasoning).
- **Extended thinking reflection prompts** (reflection.py): Three new checks when `features.extendedThinking.enabled`:
  - Synthesis without self-check: Suggests `self_check` or `verification` before concluding.
  - Missing angle exploration: Encourages `angle_exploration` or `divergence` when reasoning is too linear.
  - Adaptive thinking depth: Suggests more thinking when problem is complex (multiple stages, branches, or revisions).
- **Extended thinking metrics** (analysis.py, reflection.py): `extendedThinkingMetrics` in context/reasoningHealth: `hasSelfCheck`, `hasAngleExploration`, `branchCount`, `suggestedDepth`.
- **Config** (config.yaml, config.py): `features.extendedThinking.enabled` to toggle Claude-style prompts.

### Fixed
- **advanced_analysis.py**: `CHINESE_STOPWORDS` undefined — now correctly uses `load_chinese_stopwords()`.

### Changed
- **process_thought docstring** (server.py): Documents new thought types `self_check`, `angle_exploration`.
- **README.md**: Documents Claude-inspired extended thinking feature and new thought types.

---

## Version 0.7.4 (2026-03-12) — Tools Cleanup & Real Summary

### Removed
- **export_session** and **import_session** tools: Removed as unnecessary for typical MCP usage.
- **storage.export_session** and **storage.import_session** methods.

### Changed
- **generate_summary**: Now produces real narrative summarization instead of metadata-only:
  - `narrativeSummary`: Key points per stage, concatenated as readable text.
  - `keyFindings`: Extracted from synthesis/critique/verification/high-confidence thoughts.
  - `conclusions`: Final synthesis or last thoughts.
  - `reasoningPath`: Stage flow (e.g. "Problem Definition → Requirement Analysis → ...").
- **generate_summary** accepts optional `lang` parameter for summary language.

---

## Version 0.7.3 (2026-03-12) — Human Cognition Alignment

### Added
- **New cognitive thought types** (models.py): `divergence` (发散), `convergence` (收敛), `analogy` (类比), `question` (提问), `metacognition` (元认知) — aligned with human thinking patterns.
- **Divergence/convergence balance check** (reflection.py): Prompts when reasoning is too exploratory (no selection) or too rigid (no exploration).
- **Metacognition reminder** (reflection.py): Suggests stepping back to reflect on reasoning path after 8+ thoughts.
- **Analogy suggestion** (reflection.py): Encourages analogy when problem is complex but none used.
- **Cognitive balance metrics** (reflection.py): `reasoningHealth.cognitiveBalance` with `divergentCount`, `convergentCount`, `otherCount`.

### Changed
- **Contextual prompts** (analysis.py): Stage-specific prompts now guide divergence, convergence, critique, analogy, and metacognition.
- **Same-type streak prompt** (reflection.py): Suggests divergence, critique, verification, analogy instead of generic modes.
- **process_thought docstring** (server.py): Updated thought_type description with new cognitive types.

---

## Version 0.7.2 (2026-03-11) — HTTP Deployment & Cleanup

### Fixed
- **server.py**: `process_thought` now properly `await`s `ctx.report_progress()` to fix "coroutine was never awaited" warning.
- **server.py**: Added `TransportSecuritySettings(enable_dns_rebinding_protection=False)` so clients can connect via public IP (e.g. `106.54.55.203:8000`) without 421 Invalid Host header.
- **server.py**: Explicitly set `mcp.settings.host` and `mcp.settings.port` before `run()` so Uvicorn binds to `0.0.0.0` correctly.
- **advanced_analysis.py**: Added `token_pattern=None` for Chinese `TfidfVectorizer`; refactored `load_chinese_stopwords()` to use jieba pre-tokenization, eliminating sklearn stop_words/preprocessing mismatch warnings.

### Removed
- **Obsolete HTTP scripts**: `start_http_no_host_check.py`, `run_public_http.py`, `run_http_server.py`, `simple_http_server.py`, `simple_http_client.py`, `start_http_server.bat` — superseded by `python -m mcp_sequential_thinking.server --transport http`.
- **Test scripts**: `test_mcp_full.py`, `test_mcp_detailed.py`, `test_mcp_connection.py`.

### Changed
- **HTTP_DEPLOYMENT.md**: Recommends `python -m mcp_sequential_thinking.server` as primary startup; removed references to deleted scripts; updated Q3 auto-start example.

---

## Version 0.7.1 (2026-03-07) — Dead Code Cleanup & Database Removal

### Removed
- `debug_mcp_connection.py`: One-off debug script, not production code.
- `run_web_server.py`: FastAPI web server using stale APIs (`ThoughtStage.from_string`, removed `get_similarity_analysis`, Exa search). Incompatible with current architecture.
- `utils.py`: Zero references in codebase (unused case-conversion utilities).
- `tests/test_models.py`: Stale tests using old `ThoughtStage` enum API (`from_string`, `RESEARCH`, `ANALYSIS`, `CONCLUSION`, `validate()`).
- `tests/test_analysis.py`: Stale tests using old `ThoughtStage.RESEARCH/SYNTHESIS` enum values.
- `tests/test_storage.py`: Stale tests using old `ThoughtStorage(dir_path)` file-based API (`thought_history`, `get_thoughts_by_stage`).
- `tests/__init__.py`: Empty init file, no longer needed.

- **SQLAlchemy database**: Replaced 253-line ORM (11 tables) with 115-line in-memory list. Thoughts now live for the server process lifetime; use `export_session`/`import_session` for explicit persistence.
- **Dependencies removed**: `sqlalchemy`, `portalocker`. 
- **Optional `[web]` deps group**: Removed (FastAPI web server was deleted).
- `config.yaml` `storage` section: No longer needed.
- `StorageConfig` class from `config.py`: Removed.

### Changed
- `ThoughtStorage()` constructor no longer takes `db_url` parameter.
- Updated `README.md` project structure to reflect file removals and additions.
- Updated `.gitignore` to ignore `*.db` and `*.egg-info/`.
- Updated `pyproject.toml` version to `0.7.1`.

## Version 0.7.0 (2026-03-07) — Deep Reasoning Engine

### Added
- **`ThoughtType` cognitive operation types**: `hypothesis`, `verification`, `analysis`, `critique`, `synthesis`, `decomposition`, `observation`, `revision`. Each thought can be tagged with a type describing the cognitive operation it represents.
- **`ReflectionEngine`** (`reflection.py`): Automatic reflection prompt generator that detects 5 reasoning weakness patterns:
  - Consecutive same-type thoughts (suggests switching cognitive mode)
  - Missing critique (warns when no critical reflection for 5+ thoughts)
  - Unverified synthesis (warns about drawing conclusions without validation)
  - Confidence drops (highlights significant confidence decreases)
  - Invalid revision targets (validates `revises_thought_id` references)
- **Tree-structured reasoning**: New `parent_thought_id` field enables non-linear exploration through branching.
- **Thought revision support**: New `revises_thought_id` field allows marking corrections to earlier thoughts.
- **Branch labeling**: New `branch_label` field for organizing parallel exploration paths (e.g., "Plan A", "Plan B").
- **Reasoning health metrics**: `typeDistribution`, `branchCount`, `revisionCount`, `maxDepth` returned in reflection data.

### Changed
- `process_thought` returns a new `reflection` block alongside `analysis` with automatic reasoning feedback.
- `process_thought` now accepts `thought_type`, `parent_thought_id`, `revises_thought_id`, `branch_label` parameters.
- Database schema updated: `ThoughtModel` gains 4 new columns. **Breaking**: requires database recreation (delete old `.db` file).

## Version 0.6.0 (2026-03-07) — Architecture Refactoring

### Breaking Changes
- **`ThoughtStage`**: Changed from `Enum` to a class with string constants. The `stage` field now accepts **any string**, not just predefined enum values. This enables non-software use cases (research, business, creative writing, etc.). Predefined stages are still available as `ThoughtStage.PROBLEM_DEFINITION`, etc.
- **`process_thought`**: Parameters `tags`, `axioms_used`, `assumptions_challenged`, `supporting_evidence`, `counter_arguments` are now **Optional** (default: empty list). `confidence_level` default changed from 0.0 to 0.5.
- **`to_dict`**: Simplified output — the redundant double-conversion (loop + hardcoded override) has been replaced with direct construction.

### Removed
- **`get_similarity_analysis` tool**: Redundant — `process_thought` already returns semantic recommendations via `semanticRecommendations` in its response.
- **`suggest_next_step_prompt` prompt**: Redundant — `process_thought` already generates `suggestedPrompt` in its response when entering a new stage.
- **`debug_environment` tool**: Development-only diagnostic tool, should not be exposed to end users.
- **`search_exa` tool**: Web search functionality is outside the scope of a "sequential thinking" tool. Should be provided by a dedicated search MCP service.
- **`testing.py`**: Dead code — hardcoded test stubs previously used via `importlib.util.find_spec('pytest')` detection (removed in v0.5.0).
- **`storage_utils.py`**: Dead code — file-based storage utilities superseded by SQLAlchemy in `storage.py`, no imports remaining.
- **`validate()` method on ThoughtData**: Removed legacy no-op method. Pydantic handles validation automatically on construction.

### Changed
- **`clear_history`**: Changed from destructive `DROP TABLE` + `CREATE TABLE` to proper `DELETE` statements, preserving table schema.
- **`generate_summary`**: Added `uniqueStages` field to output (lists all stages used, including custom ones). Renamed `hasAllStages` to `hasAllPredefinedStages` for clarity.
- **`analysis.py`**: `semantic_recommendations` key renamed to camelCase `semanticRecommendations` for API consistency. `suggested_prompt` moved into the `analysis` sub-dict directly instead of being post-assigned.
- **`storage.py`**: Removed `ThoughtStage` import — stage is now stored and retrieved as plain string without enum conversion.
- **Tool count**: Reduced from 9 tools to 5 tools (process_thought, generate_summary, clear_history, export_session, import_session).


## Version 0.5.0 (2026-03-07)

### Fixed
- **config.py**: Replaced deprecated `parse_obj` with `model_validate` for Pydantic v2 compatibility
- **analysis.py**: Removed hardcoded `pytest` detection via `importlib.util.find_spec` — production code no longer imports test utilities
- **analysis.py**: Removed duplicate `import numpy as np` statement

### Changed
- **README.md**: Updated thinking stages from outdated 5-stage model (Problem Definition, Research, Analysis, Synthesis, Conclusion) to actual 6-stage software development workflow (Problem Definition, Requirement Analysis, Technical Design, Implementation, Testing and Refactoring, Integration and Deployment)
- **README.md**: Updated `generate_summary` example output to reflect 6 stages

### Code Quality Improvements

#### 1. Separation of Test Code from Production Code
- Created a new `testing.py` module for test-specific utilities
- Implemented conditional test detection using `importlib.util`
- Improved code clarity by moving test-specific logic out of main modules
- Enhanced maintainability by clearly separating test and production code paths
- Replaced hardcoded test strings with named constants

#### 2. Reduced Code Duplication in Storage Layer
- Created a new `storage_utils.py` module with shared utility functions
- Implemented reusable functions for file operations and serialization
- Standardized error handling and backup creation
- Improved consistency across serialization operations
- Optimized resource management with cleaner context handling

#### 3. API and Data Structure Improvements
- Added explicit parameter for ID inclusion in `to_dict()` method
- Created utility module with snake_case/camelCase conversion functions
- Eliminated flag-based solution in favor of explicit method parameters
- Improved readability with clearer, more explicit list comprehensions
- Eliminated duplicate calculations in analysis methods

## Version 0.4.0

### Major Improvements

#### 1. Serialization & Validation with Pydantic
- Converted `ThoughtData` from dataclass to Pydantic model
- Added automatic validation with field validators
- Maintained backward compatibility with existing code

#### 2. Thread-Safety in Storage Layer
- Added file locking with `portalocker` to prevent race conditions
- Added thread locks to protect shared data structures
- Made all methods thread-safe

#### 3. Fixed Division-by-Zero in Analysis
- Added proper error handling in `generate_summary` method
- Added safe calculation of percent complete with default values

#### 4. Case-Insensitive Stage Comparison
- Updated `ThoughtStage.from_string` to use case-insensitive comparison
- Improved user experience by accepting any case for stage names

#### 5. Added UUID to ThoughtData
- Added a unique identifier to each thought for better tracking
- Maintained backward compatibility with existing code

#### 6. Consolidated Logging Setup
- Created a central logging configuration in `logging_conf.py`
- Standardized logging across all modules

#### 7. Improved Package Entry Point
- Cleaned up the path handling in `run_server.py`
- Removed redundant code

### New Dependencies
- Added `portalocker` for file locking
- Added `pydantic` for data validation

## Version 0.3.0

Initial release with basic functionality:
- Sequential thinking process with defined stages
- Thought storage and retrieval
- Analysis and summary generation
