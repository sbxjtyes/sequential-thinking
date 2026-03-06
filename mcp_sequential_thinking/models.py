"""Data models for the sequential thinking process.

This module defines the core data structures used throughout the application,
including ThoughtStage constants and the ThoughtData Pydantic model.
"""

from typing import List, Dict, Any
from datetime import datetime
from uuid import uuid4, UUID
from pydantic import BaseModel, Field, field_validator


class ThoughtStage:
    """Predefined thinking stage constants for common workflows.

    These are provided as convenient defaults for software development scenarios.
    Any string value is accepted as a valid stage name, allowing full flexibility
    for different use cases (academic research, business analysis, creative writing, etc.).

    Example predefined stages (software development):
        - ThoughtStage.PROBLEM_DEFINITION
        - ThoughtStage.REQUIREMENT_ANALYSIS
        - ThoughtStage.TECHNICAL_DESIGN
        - ThoughtStage.IMPLEMENTATION
        - ThoughtStage.TESTING_AND_REFACTORING
        - ThoughtStage.INTEGRATION_AND_DEPLOYMENT

    Custom stages are also valid, e.g.:
        - "Literature Review"
        - "Data Collection"
        - "Market Analysis"
    """
    PROBLEM_DEFINITION = "Problem Definition"
    REQUIREMENT_ANALYSIS = "Requirement Analysis"
    TECHNICAL_DESIGN = "Technical Design"
    IMPLEMENTATION = "Implementation"
    TESTING_AND_REFACTORING = "Testing and Refactoring"
    INTEGRATION_AND_DEPLOYMENT = "Integration and Deployment"

    # All predefined stages for reference and completeness checks
    ALL = [
        PROBLEM_DEFINITION,
        REQUIREMENT_ANALYSIS,
        TECHNICAL_DESIGN,
        IMPLEMENTATION,
        TESTING_AND_REFACTORING,
        INTEGRATION_AND_DEPLOYMENT,
    ]


class ThoughtData(BaseModel):
    """Data structure for a single thought in the sequential thinking process.

    Attributes:
        thought: The main content of the thought.
        thought_number: Sequence number of this thought (1-based).
        total_thoughts: Total number of thoughts planned.
        next_thought_needed: Whether more thoughts are expected.
        stage: The thinking stage name (any string accepted).
        tags: Keywords or categories for the thought.
        axioms_used: Principles or axioms relied upon.
        assumptions_challenged: Assumptions being questioned.
        confidence_level: Confidence score between 0.0 and 1.0.
        supporting_evidence: List of supporting evidence.
        counter_arguments: List of counter-arguments.
        timestamp: ISO format timestamp of creation.
        id: Unique identifier for this thought.
    """
    thought: str
    thought_number: int
    total_thoughts: int
    next_thought_needed: bool
    stage: str = Field(
        default=ThoughtStage.PROBLEM_DEFINITION,
        description="Thinking stage name. Any string is accepted; predefined stages available in ThoughtStage."
    )
    tags: List[str] = Field(default_factory=list)
    axioms_used: List[str] = Field(default_factory=list)
    assumptions_challenged: List[str] = Field(default_factory=list)
    confidence_level: float = Field(
        default=0.5,
        description="Confidence level of the thought, between 0.0 and 1.0"
    )
    supporting_evidence: List[str] = Field(default_factory=list)
    counter_arguments: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    id: UUID = Field(default_factory=uuid4)

    def __hash__(self):
        """Make ThoughtData hashable based on its ID."""
        return hash(self.id)

    def __eq__(self, other):
        """Compare ThoughtData objects based on their ID."""
        if not isinstance(other, ThoughtData):
            return False
        return self.id == other.id

    @field_validator('thought')
    def thought_not_empty(cls, v: str) -> str:
        """Validate that thought content is not empty."""
        if not v or not v.strip():
            raise ValueError("Thought content cannot be empty")
        return v

    @field_validator('thought_number')
    def thought_number_positive(cls, v: int) -> int:
        """Validate that thought number is positive."""
        if v < 1:
            raise ValueError("Thought number must be positive")
        return v

    @field_validator('total_thoughts')
    def total_thoughts_valid(cls, v: int, values: Dict[str, Any]) -> int:
        """Validate that total thoughts >= current thought number."""
        thought_number = values.data.get('thought_number')
        if thought_number is not None and v < thought_number:
            raise ValueError("Total thoughts must be greater or equal to current thought number")
        return v

    @field_validator('confidence_level')
    def validate_confidence_level(cls, value: float) -> float:
        """Validate confidence level to be between 0.0 and 1.0."""
        if not 0.0 <= value <= 1.0:
            raise ValueError("Confidence level must be between 0.0 and 1.0")
        return value

    @field_validator('stage')
    def stage_not_empty(cls, v: str) -> str:
        """Validate that stage is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Stage cannot be empty")
        return v.strip()

    def to_dict(self, include_id: bool = False) -> dict:
        """Convert to camelCase dictionary for API output.

        Args:
            include_id: Whether to include the UUID in the output.

        Returns:
            dict: camelCase dictionary representation.
        """
        result = {
            "thought": self.thought,
            "thoughtNumber": self.thought_number,
            "totalThoughts": self.total_thoughts,
            "nextThoughtNeeded": self.next_thought_needed,
            "stage": self.stage,
            "tags": self.tags,
            "axiomsUsed": self.axioms_used,
            "assumptionsChallenged": self.assumptions_challenged,
            "confidenceLevel": self.confidence_level,
            "supportingEvidence": self.supporting_evidence,
            "counterArguments": self.counter_arguments,
            "timestamp": self.timestamp,
        }
        if include_id:
            result["id"] = str(self.id)
        return result

    @classmethod
    def from_dict(cls, data: dict) -> 'ThoughtData':
        """Create a ThoughtData instance from a camelCase or snake_case dictionary.

        Args:
            data: Dictionary containing thought data (supports both key formats).

        Returns:
            ThoughtData: A new ThoughtData instance.
        """
        # camelCase → snake_case mapping
        mappings = {
            "thoughtNumber": "thought_number",
            "totalThoughts": "total_thoughts",
            "nextThoughtNeeded": "next_thought_needed",
            "axiomsUsed": "axioms_used",
            "assumptionsChallenged": "assumptions_challenged",
            "confidenceLevel": "confidence_level",
            "supportingEvidence": "supporting_evidence",
            "counterArguments": "counter_arguments",
        }

        snake_data = {}

        # Process known camelCase → snake_case mappings
        for camel_key, snake_key in mappings.items():
            if camel_key in data:
                snake_data[snake_key] = data[camel_key]

        # Copy fields that are the same in both formats
        for key in ["thought", "stage", "tags", "timestamp"]:
            if key in data:
                snake_data[key] = data[key]

        # Also accept snake_case keys directly (for flexibility)
        for key in ["thought_number", "total_thoughts", "next_thought_needed",
                     "axioms_used", "assumptions_challenged", "confidence_level",
                     "supporting_evidence", "counter_arguments"]:
            if key in data and key not in snake_data:
                snake_data[key] = data[key]

        # Defaults for list fields
        snake_data.setdefault("tags", [])
        snake_data.setdefault("axioms_used", [])
        snake_data.setdefault("assumptions_challenged", [])
        snake_data.setdefault("supporting_evidence", [])
        snake_data.setdefault("counter_arguments", [])
        snake_data.setdefault("timestamp", datetime.now().isoformat())

        # Handle UUID
        if "id" in data:
            try:
                snake_data["id"] = UUID(data["id"])
            except (ValueError, TypeError):
                snake_data["id"] = uuid4()

        return cls(**snake_data)

    model_config = {
        "arbitrary_types_allowed": True
    }
