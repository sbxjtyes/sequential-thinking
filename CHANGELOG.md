# Changelog

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
