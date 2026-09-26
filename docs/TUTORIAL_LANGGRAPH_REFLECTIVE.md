# LangGraph reflective workflow
Install `pip install -e ".[langgraph]"`. Construct an engine, then:
```python
from sraf.core.engine import ReflectionEngine
from sraf.core.models import Policy
from sraf.core.providers import FixtureJudge, FixtureGenerator
from sraf.framework_adapters.langgraph_reflective_adapter import build_graph
engine = ReflectionEngine(FixtureJudge(), FixtureGenerator(), Policy())
graph = build_graph(lambda prompt: "Initial answer", engine)
state = graph.invoke({"prompt": "What happened?", "evidence": "Log: degraded"})
print(state["result"]["metrics"])
```
The `generate → reflect` edge is explicit. For native regeneration nodes, split the core iteration and route conditionally; never wire back to side-effecting tool nodes. Replace fixtures and calibrate independently before real deployment.
