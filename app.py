import time
import streamlit as st
from engine import PipelineEngine
from runner import AgentRegistry, DynamicResearchAgent, FinancialAnalystAgent, WorkflowRunner
from schemas import PipelineRun, Step, StepStatus

# Page Configuration
st.set_page_config(
    page_title="Autonomous Multi-Agent Control Plane",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS Styling for High-Performance UI
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #ff4b4b; color: white; font-weight: bold; border-radius: 4px; }
    .metric-card { background-color: #1f2937; padding: 15px; border-radius: 8px; border: 1px solid #374151; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Autonomous Multi-Agent Orchestration Engine")
st.markdown("---")

# 1. Initialize Pipeline Topology & Registry
def get_initialized_engine(task_prompt: str) -> PipelineEngine:
    steps = [
        Step(step_id="step_0_research", order=0, agent_role="Researcher", status=StepStatus.QUEUED),
        Step(step_id="step_1_audit", order=1, agent_role="Financial_Analyst", status=StepStatus.QUEUED)
    ]
    run_state = PipelineRun(
        run_id="run_live_01",
        task_description=task_prompt,
        steps=steps,
        overall_status=StepStatus.QUEUED
    )
    engine = PipelineEngine(run_state)
    return engine

# 2. Sidebar Configuration & Input Controls
with st.sidebar:
    st.header("🎯 Mission Parameters")
    user_prompt = st.text_area(
        "Enter Objective / Prompt",
        value="Plan a 3-day budget trip to Goa under 25000 INR including transport and stay.",
        height=100
    )
    launch_btn = st.button("Execute Pipeline")

# 3. Execution Control Plane Flow
if launch_btn:
    if not user_prompt.strip():
        st.error("Mission objective cannot be empty.")
    else:
        engine = get_initialized_engine(user_prompt)
        
        # Setup Registry & Runner
        registry = AgentRegistry()
        registry.register("Researcher", DynamicResearchAgent())
        registry.register("Financial_Analyst", FinancialAnalystAgent())
        
        runner = WorkflowRunner(engine, registry)

        st.subheader("🚀 Live Execution Trace")
        
        status_container = st.container()
        with status_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_steps = len(engine.run.steps)
            while engine.run.overall_status not in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.PAUSED]:
                current_idx = engine.run.current_step_index
                if current_idx >= total_steps:
                    break
                
                active_step = engine.run.steps[current_idx]
                status_text.markdown(f"Executing [{active_step.agent_role.upper()}]: Running step {active_step.step_id}...")
                
                step_status = runner.run_next_step()
                
                progress_bar.progress((current_idx + 1) / total_steps)
                time.sleep(0.4)

            if engine.run.overall_status == StepStatus.COMPLETED:
                status_text.markdown("### ✅ Pipeline Execution Successfully Completed (Gate >= 85.0 Passed)")
            else:
                status_text.markdown(f"### ⚠️ Pipeline Halted. Status: {engine.run.overall_status}")

# 4. Render Agent Chain-of-Custody Trace & Binary Status Badges
        st.markdown("---")
        st.subheader("📂 Immutable Checkpoint Artifacts & Agent Payloads")

        if engine.run.checkpoints:
            for idx, cp in enumerate(engine.run.checkpoints):
                role_label = "🔍 Agent 1: Dynamic Researcher" if idx == 0 else "📊 Agent 2: Financial Analyst"
                
                # Derive binary categorical status from payload content
                is_completed = "STATUS: COMPLETED" in cp.output_data
                status_badge = "🟢 COMPLETED" if is_completed else "🔴 FAILED / BLOCKED"
                
                with st.expander(f"Step {idx}: {cp.step_id} — [{role_label}] | Status: {status_badge}", expanded=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown("*Agent Output Payload:*")
                        st.markdown(cp.output_data)
                    with col2:
                        st.markdown("*Telemetry State:*")
                        st.markdown(f"*Handoff Protocol:* {status_badge}")
                        st.markdown(f"*Timestamp:* {cp.timestamp}")
        else:
           st.info("No chain-of-custody checkpoints committed yet.")       

else:
    st.info("Configure your target parameters in the sidebar and click Execute Pipeline to launch the multi-agent control plane.")