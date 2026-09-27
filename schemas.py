from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
from typing import Optional

# 1. Finite State Machine Contract for Agents
class StepStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"

# 2. Confidence Gate Contract (Differentiator #4)
class ValidationBreakdown(BaseModel):
    evidence_grounding: float = Field(default=0.0, ge=0.0, le=30.0)
    consistency: float = Field(default=0.0, ge=0.0, le=20.0)
    schema_format: float = Field(default=0.0, ge=0.0, le=10.0)
    tool_verification: float = Field(default=0.0, ge=0.0, le=20.0)
    cross_check: float = Field(default=0.0, ge=0.0, le=20.0)

    @property
    def total_score(self) -> float:
        return (
            self.evidence_grounding
            + self.consistency
            + self.schema_format
            + self.tool_verification
            + self.cross_check
        )
    # Differentiator #3: Immutable State Persistence
class Checkpoint(BaseModel):
    model_config = ConfigDict(frozen=True)  # Read-only snapshot
    checkpoint_id: str
    step_id: str
    output_data: str
    validation_score: float = Field(ge=85.0, le=100.0)  # Rejects unverified state
    timestamp: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))
# Resource Telemetry Contract (Differentiator #5)
class UsageMetrics(BaseModel):
    duration_seconds: float = Field(default=0.0, ge=0.0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)

# Atomic Orchestration Unit
class Step(BaseModel):
    step_id: str
    order: int
    agent_role: str
    status: StepStatus = StepStatus.QUEUED
    input_payload: Optional[str] = None
    output_payload: Optional[str] = None
    validation: Optional[ValidationBreakdown] = None
    metrics: Optional[UsageMetrics] = None

# Aggregate Root: Multi-Agent Orchestration State Machine
class PipelineRun(BaseModel):
    run_id: str
    task_description: str
    steps: list[Step] = Field(default_factory=list)
    checkpoints: list[Checkpoint] = Field(default_factory=list)
    current_step_index: int = Field(default=0, ge=0)
    overall_status: StepStatus = StepStatus.QUEUED    