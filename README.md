finguard_engine/
├── schemas.py      # Core data contracts, FSM enums, validation breakdowns, & telemetry
├── engine.py       # State engine, confidence gate evaluator, disk persistence & rehydration
├── runner.py       # Agent registry, polymorphic execution workers, & live API loops
└── app.py          # Streamlit live control plane and real-time execution visualization UI
