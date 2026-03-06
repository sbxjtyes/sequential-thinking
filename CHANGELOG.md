# Changelog

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
