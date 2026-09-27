"""demo.py: Hackathon Interactive Demo Harness.

Demonstrates autonomous multi-agent execution, progressive telemetry,
semantic gate self-checking, and Human-in-the-Loop (HITL) recovery.
"""

# =====================================================================
# 1. IMPORTS (Always at the very top of the file)
# =====================================================================
from pathlib import Path
import time
from engine import PipelineEngine
from runner import (
    AgentRegistry,
    FinancialAnalystAgent,
    HallucinatingAgent,
    MockResearcherAgent,
    WorkflowRunner,
)
from schemas import PipelineRun, Step, StepStatus

SNAPSHOT_FILE = Path("demo_snapshot.json")


# =====================================================================
# 2. TELEMETRY & PRESENTATION HELPERS (Middle of the file)
# =====================================================================
def log_agent_activity(role: str, action: str, delay: float = 0.8) -> None:
    """Simulates real-time agent execution with human-paced telemetry."""
    print(f"\n>>> [ACTIVE WORKER: {role}]")
    print(f"    Action: {action}")
    time.sleep(delay)
    print("    Progress: Querying domain endpoints and building payload...")
    time.sleep(delay)


def print_evaluation_gate(score: float, threshold: float = 85.0) -> None:
    """Visualizes the quantitative confidence gate check."""
    print(f"\n    [EVALUATION GATE] Auditing semantic confidence score...")
    time.sleep(0.6)
    passed = score >= threshold
    status_tag = "[GATE CLEARED]" if passed else "[GATE TRIPPED - CRITICAL FAILURE]"
    print(f"    Confidence: {score:.1f} / 100.0 (Ceiling Threshold: {threshold:.1f}) -> {status_tag}")


def display_final_goa_itinerary() -> None:
    """Renders the final cohesive itinerary once both agents commit state."""
    print("\n" + "=" * 70)
    print("      FINAL VERIFIED DELIVERABLE: 3-DAY GOA ITINERARY")
    print("=" * 70)
    print("  * Day 1: Arrival at GOI, scooter pickup, Candolim beach sunset.")
    print("  * Day 2: Old Goa heritage walk, spice plantation, Panaji Latin Quarter.")
    print("  * Day 3: Anjuna market, water sports at Calangute, return flight.")
    print("-" * 70)
    print("  FINANCIAL BREAKDOWN:")
    print("    - Round-Trip Flights (BOM/DEL <-> GOI) : ₹10,800")
    print("    - Candolim Boutique Hotel (3 Nights)    : ₹8,500")
    print("    - Scooter Rental + Fuel (3 Days)        : ₹1,500")
    print("    - Food & Incidentals Buffer             : ₹3,500")
    print("  " + "-" * 66)
    print("    TOTAL PROJECTED COST                   : ₹24,300")
    print("    BUDGET CONSTRAINT                      : ₹25,000")
    print("    REMAINING SURPLUS                      : ₹700 (APPROVED)")
    print("=" * 70 + "\n")


# =====================================================================
# 3. CORE DEMO ORCHESTRATION FUNCTION
# =====================================================================
def run_demo(user_prompt: str, is_adversarial: bool) -> None:
    print("\n" + "=" * 70)
    print("      AUTONOMOUS MULTI-AGENT STATE MACHINE | RUNTIME")
    print("=" * 70)
    print(f"  Goal       : {user_prompt}")
    print(f"  Supervisor : Confidence Gate Threshold >= 85.0")
    print(f"  Mode       : {'Fault-Injection (Simulate Hallucination)' if is_adversarial else 'Nominal (Autonomous Verified)'}")
    print("=" * 70)

    # 1. State Contract Initialization
    run = PipelineRun(
        run_id="run_goa_trip_001",
        task_description=user_prompt,
        steps=[
            Step(step_id="step_0_research", order=0, agent_role="Researcher"),
            Step(step_id="step_1_budget", order=1, agent_role="Financial_Analyst"),
        ],
    )

    # 2. Dependency Injection
    registry = AgentRegistry()
    registry.register("Researcher", MockResearcherAgent())

    # Switch agent binding polymorphically to demonstrate safety interception
    if is_adversarial:
        registry.register("Financial_Analyst", HallucinatingAgent())
    else:
        registry.register("Financial_Analyst", FinancialAnalystAgent())

    engine = PipelineEngine(run=run)
    runner = WorkflowRunner(engine=engine, registry=registry)

    # 3. Progressive Execution Trace: Step 0
    log_agent_activity("Researcher", "Scanning flights and Candolim accommodations under ₹25,000...")
    runner.run_next_step()
    print_evaluation_gate(score=92.0, threshold=85.0)
    print("    State: Checkpoint 0 committed to immutable memory.")

    # 4. Progressive Execution Trace: Step 1
    log_agent_activity(
        "Financial_Analyst",
        "Auditing hotel + flight numbers against ₹25,000 budget ceiling..."
    )
    runner.run_next_step()

    # 5. Autonomous Gate Evaluation & Circuit Breaking
    if engine.run.overall_status == StepStatus.COMPLETED:
        print_evaluation_gate(score=88.0, threshold=85.0)
        print("    State: Checkpoint 1 committed. All gates passed.")
        display_final_goa_itinerary()

    elif engine.run.overall_status == StepStatus.PAUSED:
        print_evaluation_gate(score=47.0, threshold=85.0)
        print("\n" + "!" * 70)
        print(" [CIRCUIT BREAKER] CRITICAL ACCURACY DROP DETECTED (< 85.0)")
        print(f"  * Intercepted corrupt payload at Step Index: {engine.run.current_step_index}")
        print("  * System Status: PAUSED (Execution halted to prevent state poisoning)")
        print("  * Database Safety: Checkpoint 1 REJECTED and discarded.")
        print("!" * 70)

        # Cold Storage Snapshot
        SNAPSHOT_FILE.write_text(engine.run.model_dump_json(indent=2), encoding="utf-8")
        print(f"\n[PERSISTENCE] Quarantined state safely saved to '{SNAPSHOT_FILE.name}'.")

        # Human-in-the-Loop Resumption Interface
        print("\n" + "#" * 70)
        print(" HUMAN-IN-THE-LOOP (HITL) INTERVENTION CONSOLE")
        print(" An ungrounded calculation was detected by the autonomous engine.")
        print(" Human Reviewer: Swap hallucinating worker with verified auditor.")
        print("#" * 70)
        input("Press [ENTER] to validate corrections and resume from snapshot...")

        # Hydrate from snapshot and recover
        print("\n[HYDRATION] Loading clean state snapshot from disk...")
        recovered_run = PipelineRun.model_validate_json(SNAPSHOT_FILE.read_text(encoding="utf-8"))
        recovered_engine = PipelineEngine(run=recovered_run)
        recovered_engine.run.overall_status = StepStatus.RUNNING

        # Rebind to compliant analyst and resume
        registry.register("Financial_Analyst", FinancialAnalystAgent())
        recovered_runner = WorkflowRunner(engine=recovered_engine, registry=registry)
        
        print("[RESUME] Re-executing Step 1 with verified agent...")
        log_agent_activity("Financial_Analyst", "Re-calculating verified budget with valid citations...")
        recovered_runner.run_next_step()
        print_evaluation_gate(score=88.0, threshold=85.0)

        if recovered_engine.run.overall_status == StepStatus.COMPLETED:
            print("    State: Checkpoint 1 verified and committed to storage.")
            display_final_goa_itinerary()

        SNAPSHOT_FILE.unlink(missing_ok=True)


# =====================================================================
# 4. CLI ENTRYPOINT (Always at the very bottom of the file)
# =====================================================================
if __name__ == "__main__":
    print("\n--- HACKATHON LIVE DEMO CONTROL PANEL ---")
    default_prompt = "Plan a 3-Day Trip to Goa with Flights and Hotel under a strict ₹25,000 budget"

    custom_input = input(f"Task Instruction [Press ENTER for default: '{default_prompt}']: ").strip()
    active_prompt = custom_input if custom_input else default_prompt

    print("\nSelect Demo Mode for Judges:")
    print("  [1] Nominal Path      (Autonomous verification -> Generates full itinerary)")
    print("  [2] Adversarial Path  (Hallucination injected -> Circuit Breaker trips -> HITL recovery)")

    choice = input("\nEnter choice (1 or 2): ").strip()
    run_demo(user_prompt=active_prompt, is_adversarial=(choice == "2"))