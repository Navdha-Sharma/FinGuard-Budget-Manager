import uuid
from schemas import (
    Checkpoint,
    PipelineRun,
    Step,
    StepStatus,
    UsageMetrics,
    ValidationBreakdown,
)

class PipelineEngine:
    def __init__(self, run: PipelineRun):
        self.run = run

    def process_step_result(
        self,
        output_payload: str,
        validation: ValidationBreakdown,
        metrics: UsageMetrics,
    ) -> StepStatus:
        """
        Evaluates step output against the confidence gate (Differentiator #4),
        creates an immutable Checkpoint if >= 85.0 (Differentiator #3),
        or transitions the pipeline to PAUSED for human review.
        """
        # Engine logic will be built here socratically
        # 1. Guard Clause: Short-circuit if pipeline has already finished
        if self.run.current_step_index >= len(self.run.steps):
            self.run.overall_status = StepStatus.COMPLETED
            return self.run.overall_status

        # 2. Extract Reference to the Active Step
        current_step: Step = self.run.steps[self.run.current_step_index]

        # 3. Bind Incoming Payloads & Telemetry
        current_step.output_payload = output_payload
        current_step.validation = validation
        current_step.metrics = metrics
        # 4. Confidence Gate Decision & Checkpoint Persistence
        score = validation.total_score
        if score >= 85.0:
            # Construct immutable snapshot of verified work
            checkpoint = Checkpoint(
                checkpoint_id=f"chk_{uuid.uuid4().hex[:8]}",
                step_id=current_step.step_id,
                output_data=output_payload,
                validation_score=score,
            )
            self.run.checkpoints.append(checkpoint)
            current_step.status = StepStatus.COMPLETED
            self.run.current_step_index += 1

            # Advance pipeline lifecycle
            if self.run.current_step_index >= len(self.run.steps):
                self.run.overall_status = StepStatus.COMPLETED
            else:
                self.run.overall_status = StepStatus.RUNNING
        else:
            # Gate Failure: Pause execution for human review
            current_step.status = StepStatus.PAUSED
            self.run.overall_status = StepStatus.PAUSED

        return self.run.overall_status
    def export_state(self, filepath: str) -> None:
        """Serializes the aggregate root to disk as a JSON snapshot."""
        json_data = self.run.model_dump_json(indent=2)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_data)

    @classmethod
    def rehydrate(cls, filepath: str) -> "PipelineEngine":
        """Restores a PipelineEngine instance from a persisted JSON snapshot."""
        with open(filepath, "r", encoding="utf-8") as f:
            json_data = f.read()
        restored_run = PipelineRun.model_validate_json(json_data)
        return cls(run=restored_run)

    def resolve_paused_step(
        self,
        corrected_payload: str,
        new_validation: ValidationBreakdown,
        new_metrics: UsageMetrics,
    ) -> StepStatus:
        """
        Human-in-the-loop intervention handler. Re-evaluates a PAUSED step.
        """
        # Guard: Only paused workflows can be manually resolved
        if self.run.overall_status != StepStatus.PAUSED:
            raise ValueError(
                f"Cannot resolve pipeline in status: {self.run.overall_status}. "
                "Only PAUSED pipelines accept manual intervention."
            )

        current_step: Step = self.run.steps[self.run.current_step_index]

        # 1. Update payload and validation breakdown
        current_step.output_payload = corrected_payload
        current_step.validation = new_validation

        # 2. Accumulate Telemetry (Differentiator #5: Retain total cost)
        if current_step.metrics is not None:
            current_step.metrics.duration_seconds += new_metrics.duration_seconds
            current_step.metrics.input_tokens += new_metrics.input_tokens
            current_step.metrics.output_tokens += new_metrics.output_tokens
            current_step.metrics.estimated_cost_usd += new_metrics.estimated_cost_usd
        else:
            current_step.metrics = new_metrics

        # 3. Re-evaluate Confidence Gate (Differentiator #4: Threshold >= 85.0)
        score = new_validation.total_score
        if score >= 85.0:
            checkpoint = Checkpoint(
                checkpoint_id=f"chk_{uuid.uuid4().hex[:8]}",
                step_id=current_step.step_id,
                output_data=corrected_payload,
                validation_score=score,
            )
            self.run.checkpoints.append(checkpoint)
            current_step.status = StepStatus.COMPLETED
            self.run.current_step_index += 1

            if self.run.current_step_index >= len(self.run.steps):
                self.run.overall_status = StepStatus.COMPLETED
            else:
                self.run.overall_status = StepStatus.RUNNING
        else:
            current_step.status = StepStatus.PAUSED
            self.run.overall_status = StepStatus.PAUSED

        return self.run.overall_status

if __name__ == "__main__":
    # --- PHASE 1: ALLOCATE STATE MACHINE & WORKFLOW AGGREGATE ---
    test_run = PipelineRun(
        run_id="run_test_001",
        task_description="Multi-agent market analysis harness test",
        steps=[
            Step(step_id="step_1", order=0, agent_role="Researcher"),
            Step(step_id="step_2", order=1, agent_role="Financial_Analyst"),
        ],
    )
    engine = PipelineEngine(run=test_run)

    # --- PHASE 2: TEST 1 - CONFIDENCE GATE PASS (Score >= 85.0) ---
    print("--- [TEST 1: Confidence Gate PASS (Score >= 85)] ---")
    pass_validation = ValidationBreakdown(
        evidence_grounding=28.0,
        consistency=19.0,
        schema_format=10.0,
        tool_verification=18.0,
        cross_check=18.0,  # Total Score = 93.0
    )
    pass_metrics = UsageMetrics(
        duration_seconds=1.42,
        input_tokens=450,
        output_tokens=180,
        estimated_cost_usd=0.003,
    )

    # Execute step 1
    status_1 = engine.process_step_result(
        output_payload="Verified Market Data",
        validation=pass_validation,
        metrics=pass_metrics,
    )

    # Assert Test 1 State Invariants
    assert test_run.steps[0].status == StepStatus.COMPLETED, "Step 1 must be COMPLETED"
    assert test_run.current_step_index == 1, "Pointer must advance to index 1"
    assert len(test_run.checkpoints) == 1, "One immutable checkpoint must be created"
    print("Test 1 Passed: Checkpoint created and pointer advanced.")

    # --- PHASE 3: TEST 2 - CONFIDENCE GATE FAIL (Score < 85.0) ---
    print("\n--- [TEST 2: Confidence Gate FAIL (Score < 85)] ---")
    fail_validation = ValidationBreakdown(
        evidence_grounding=15.0,
        consistency=12.0,
        schema_format=8.0,
        tool_verification=15.0,
        cross_check=10.0,  # Total Score = 60.0
    )
    fail_metrics = UsageMetrics(
        duration_seconds=0.85,
        input_tokens=320,
        output_tokens=90,
        estimated_cost_usd=0.001,
    )

    # Execute step 2 (should fail the gate)
    status_2 = engine.process_step_result(
        output_payload="Hallucinated Analysis",
        validation=fail_validation,
        metrics=fail_metrics,
    )

    # Assert Test 2 State Invariants
    assert test_run.steps[1].status == StepStatus.PAUSED, "Step 2 must be PAUSED"
    assert test_run.overall_status == StepStatus.PAUSED, "Pipeline run must be PAUSED"
    assert test_run.current_step_index == 1, "Pointer must NOT advance on gate failure"
    assert len(test_run.checkpoints) == 1, "No checkpoint should be appended for failed step"
    print("Test 2 Passed: Pipeline paused deterministically. Zero state corruption.")
    # --- PHASE 4: STATE EXPORT & REHYDRATION (Differentiator #3) ---
    print("\n--- [TEST 3: State Export & Rehydration] ---")
    snapshot_path = "pipeline_snapshot.json"
    engine.export_state(snapshot_path)
    print(f"Exported pipeline state to {snapshot_path}")

    # Rehydrate into a completely new engine instance (simulating process restart)
    restored_engine = PipelineEngine.rehydrate(snapshot_path)
    assert restored_engine.run.run_id == test_run.run_id, "Run ID mismatch after rehydration"
    assert restored_engine.run.current_step_index == 1, "Pointer must remain at step 1"
    assert restored_engine.run.overall_status == StepStatus.PAUSED, "Restored status must be PAUSED"
    assert len(restored_engine.run.checkpoints) == 1, "Restored checkpoints count mismatch"
    print("Test 3 Passed: State rehydrated flawlessly from disk snapshot.")

    # --- PHASE 5: HUMAN-IN-THE-LOOP RESOLUTION (Differentiator #4 & #5) ---
    print("\n--- [TEST 4: HITL Intervention & Telemetry Accumulation] ---")
    corrected_validation = ValidationBreakdown(
        evidence_grounding=26.0,
        consistency=18.0,
        schema_format=10.0,
        tool_verification=18.0,
        cross_check=18.0,  # Total Score = 90.0 (Passes >= 85.0 gate)
    )
    intervention_metrics = UsageMetrics(
        duration_seconds=1.10,
        input_tokens=200,
        output_tokens=150,
        estimated_cost_usd=0.002,
    )

    # Resolve the paused step via the rehydrated engine
    final_status = restored_engine.resolve_paused_step(
        corrected_payload="Human Corrected Market Analysis",
        new_validation=corrected_validation,
        new_metrics=intervention_metrics,
    )

    # Assert Resolution Invariants
    resolved_step = restored_engine.run.steps[1]
    assert resolved_step.status == StepStatus.COMPLETED, "Resolved step must be COMPLETED"
    assert restored_engine.run.overall_status == StepStatus.COMPLETED, "Pipeline must be fully COMPLETED"
    assert restored_engine.run.current_step_index == 2, "Pointer must advance to index 2"
    assert len(restored_engine.run.checkpoints) == 2, "Second checkpoint must be committed"

    # Assert Telemetry Accumulation (Original 0.85s + Retry 1.10s = 1.95s)
    expected_duration = round(0.85 + 1.10, 2)
    actual_duration = round(resolved_step.metrics.duration_seconds, 2)
    assert actual_duration == expected_duration, f"Telemetry duration not accumulated: {actual_duration}"
    assert resolved_step.metrics.input_tokens == 520, "Input tokens must accumulate (320 + 200 = 520)"
    print("Test 4 Passed: HITL intervention passed gate, telemetry accumulated, workflow completed.")

    print("\nAll State Machine Invariants & Recovery Lifecycles Verified Successfully.")

    print("\nAll State Machine Invariants Verified Successfully.")    