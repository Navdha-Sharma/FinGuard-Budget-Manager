finguard_engine/

1 .├── schemas.py      # Core data contracts, FSM enums, validation breakdowns, & telemetry

2 ├── engine.py       # State engine, confidence gate evaluator, disk persistence & rehydration

3 ├── runner.py       # Agent registry, polymorphic execution workers, & live API loops

4 └── app.py          # Streamlit live control plane and real-time execution visualization UI
