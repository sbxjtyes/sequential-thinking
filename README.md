[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/arben-adm-mcp-sequential-thinking-badge.png)](https://mseep.ai/app/arben-adm-mcp-sequential-thinking)

# Sequential Thinking MCP Server

A Model Context Protocol (MCP) server that facilitates structured, progressive thinking through defined stages. This tool helps break down complex problems into sequential thoughts, track the progression of your thinking process, and generate summaries.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<a href="https://glama.ai/mcp/servers/m83dfy8feg"><img width="380" height="200" src="https://glama.ai/mcp/servers/m83dfy8feg/badge" alt="Sequential Thinking Server MCP server" /></a>

## Features

- **Structured Thinking Framework**: Organizes thoughts through customizable stages. Comes with predefined software development stages (Problem Definition, Requirement Analysis, Technical Design, etc.), but accepts **any string** as a stage name for full flexibility across use cases (research, business analysis, creative writing, etc.)
- **Thought Tracking**: Records and manages sequential thoughts with metadata
- **Related Thought Analysis**: Identifies connections between similar thoughts
- **Progress Monitoring**: Tracks your position in the overall thinking sequence
- **Summary Generation**: Creates concise overviews of the entire thought process
- **Persistent Storage**: Automatically saves your thinking sessions with thread-safety
- **Data Import/Export**: Share and reuse thinking sessions
- **Extensible Architecture**: Easily customize and extend functionality
- **Robust Error Handling**: Graceful handling of edge cases and corrupted data
- **Type Safety**: Comprehensive type annotations and validation

## Prerequisites

- Python 3.10 or higher
- UV package manager ([Install Guide](https://github.com/astral-sh/uv))

## Key Technologies

- **Pydantic**: For data validation and serialization
- **SQLAlchemy**: For database-backed persistent storage
- **FastMCP**: For Model Context Protocol integration
- **scikit-learn + jieba**: For TF-IDF semantic similarity analysis (Chinese & English)
- **PyYAML**: For configuration management

## Project Structure

```
mcp-sequential-thinking/
├── mcp_sequential_thinking/
│   ├── server.py           # Main server implementation and MCP tools
│   ├── models.py           # Data models with Pydantic validation
│   ├── storage.py          # SQLAlchemy-backed persistence layer
│   ├── analysis.py         # Thought analysis and pattern detection
│   ├── advanced_analysis.py # TF-IDF semantic similarity engine
│   ├── config.py           # Configuration loading from YAML
│   ├── reflection.py       # Automatic reflection engine for reasoning QA
│   ├── logging_conf.py     # Centralized logging configuration
│   └── __init__.py         # Package initialization
├── run_server.py       # Server entry point script
├── README.md           # Main documentation
├── CHANGELOG.md        # Version history and changes
├── example.md          # Future development plan
├── LICENSE             # MIT License
└── pyproject.toml      # Project configuration and dependencies
```

## Quick Start

1. **Set Up Project**
   ```bash
   # Create and activate virtual environment
   uv venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Unix

   # Install package and dependencies
   uv pip install -e .

   # For development with testing tools
   uv pip install -e ".[dev]"

   # For all optional dependencies
   uv pip install -e ".[all]"
   ```

2. **Run the Server**
   ```bash
   # Run directly
   uv run -m mcp_sequential_thinking.server

   # Or use the installed script
   mcp-sequential-thinking
   ```

3. **Run Tests**
   ```bash
   # Run all tests
   pytest

   # Run with coverage report
   pytest --cov=mcp_sequential_thinking
   ```

## Claude Desktop Integration

Add to your Claude Desktop configuration (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\your\\mcp-sequential-thinking\\run_server.py",
        "run",
        "server.py"
        ]
      }
    }
  }
```

Alternatively, if you've installed the package with `pip install -e .`, you can use:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "mcp-sequential-thinking"
    }
  }
}
```

You can also run it directly using uvx and skipping the installation step:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/arben-adm/mcp-sequential-thinking",
        "--with",
        "portalocker",
        "mcp-sequential-thinking"
      ]
    }
  }
}
```

# How It Works

The server maintains a history of thoughts and processes them through a structured workflow. Each thought is validated using Pydantic models, categorized into thinking stages, and stored with relevant metadata in a thread-safe storage system. The server automatically handles data persistence, backup creation, and provides tools for analyzing relationships between thoughts.

## Usage Guide

The Sequential Thinking server exposes five tools:

### 1. `process_thought`

Records and analyzes a new thought in your sequential thinking process.

**Parameters:**

- `thought` (string, required): The content of your thought
- `thought_number` (integer, required): Position in your sequence (e.g., 1 for first thought)
- `total_thoughts` (integer, required): Expected total thoughts in the sequence
- `next_thought_needed` (boolean, required): Whether more thoughts are needed after this one
- `stage` (string, optional): The thinking stage. **Any string is accepted.** Predefined stages include:
  - "Problem Definition" (default)
  - "Requirement Analysis"
  - "Technical Design"
  - "Implementation"
  - "Testing and Refactoring"
  - "Integration and Deployment"
  - Or any custom stage: "Literature Review", "Data Collection", "Market Analysis", etc.
- `tags` (list of strings, optional): Keywords or categories for your thought
- `axioms_used` (list of strings, optional): Principles or axioms applied in your thought
- `assumptions_challenged` (list of strings, optional): Assumptions your thought questions or challenges
- `confidence_level` (float, optional): Confidence score between 0.0 and 1.0, defaults to 0.5
- `supporting_evidence` (list of strings, optional): Evidence supporting the thought
- `counter_arguments` (list of strings, optional): Counter-arguments to consider
- `lang` (string, optional): Language for analysis ('en' or 'zh'), defaults to config setting

**Example:**

```python
# Minimal call - only 4 required params
process_thought(
    thought="The problem of climate change requires multifaceted analysis.",
    thought_number=1,
    total_thoughts=5,
    next_thought_needed=True
)

# Full call with optional metadata
process_thought(
    thought="The problem of climate change requires analysis of multiple factors.",
    thought_number=1,
    total_thoughts=5,
    next_thought_needed=True,
    stage="Problem Definition",
    tags=["climate", "global policy"],
    confidence_level=0.8
)

# Custom stages for non-software use cases
process_thought(
    thought="Reviewing existing literature on neural network pruning techniques.",
    thought_number=1,
    total_thoughts=6,
    next_thought_needed=True,
    stage="Literature Review"
)
```

### 2. `generate_summary`

Generates a summary of your entire thinking process.

**Example output:**

```json
{
  "summary": {
    "totalThoughts": 6,
    "stages": {
      "Problem Definition": 1,
      "Requirement Analysis": 1,
      "Technical Design": 1,
      "Implementation": 1,
      "Testing and Refactoring": 1,
      "Integration and Deployment": 1
    },
    "timeline": [
      {"number": 1, "stage": "Problem Definition"},
      {"number": 2, "stage": "Requirement Analysis"},
      {"number": 3, "stage": "Technical Design"},
      {"number": 4, "stage": "Implementation"},
      {"number": 5, "stage": "Testing and Refactoring"},
      {"number": 6, "stage": "Integration and Deployment"}
    ]
  }
}
```

### 3. `clear_history`

Resets the thinking process by clearing all recorded thoughts.

### 4. `export_session`

Exports the entire thinking session to a local JSON file for archiving or sharing.

**Parameters:**
- `file_path` (string): Absolute path for saving the session file

### 5. `import_session`

Imports a previously exported thinking session from a JSON file. Overwrites current session.

## Practical Applications

- **Decision Making**: Work through important decisions methodically
- **Problem Solving**: Break complex problems into manageable components
- **Research Planning**: Structure your research approach with clear stages
- **Writing Organization**: Develop ideas progressively before writing
- **Project Analysis**: Evaluate projects through defined analytical stages


## Getting Started

With the proper MCP setup, simply use the `process_thought` tool to begin working through your thoughts in sequence. As you progress, you can get an overview with `generate_summary` and reset when needed with `clear_history`.



# Customizing the Sequential Thinking Server

For detailed examples of how to customize and extend the Sequential Thinking server, see [example.md](example.md). It includes code samples for:

- Modifying thinking stages
- Enhancing thought data structures with Pydantic
- Adding persistence with databases
- Implementing enhanced analysis with NLP
- Creating custom prompts
- Setting up advanced configurations
- Building web UI integrations
- Implementing visualization tools
- Connecting to external services
- Creating collaborative environments
- Separating test code
- Building reusable utilities




## License

MIT License



