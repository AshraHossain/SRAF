---
paths:
  - "src/sraf/**/*.py"
  - "policies/**/*.json"
---
# SRAF Policy & Reflection Rules (`src/sraf/`)
1. Quality thresholds, max regeneration rounds, and cost ceilings must be enforced deterministically in Python.
2. Policies must fail closed on unknown or forbidden tool calls.
