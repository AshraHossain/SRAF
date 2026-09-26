from typing import TypedDict

from sraf.core.engine import ReflectionEngine


class State(TypedDict, total=False):
    prompt: str
    evidence: str
    draft: str
    result: dict

def build_graph(produce, engine: ReflectionEngine):
    from langgraph.graph import END, START, StateGraph
    def generate(state: State) -> dict:
        return {"draft": produce(state["prompt"])}
    def reflect(state: State) -> dict:
        from dataclasses import asdict
        return {"result": asdict(engine.run(state["prompt"], state["draft"], state.get("evidence", "")))}
    graph = StateGraph(State)
    graph.add_node("generate", generate)
    graph.add_node("reflect", reflect)
    graph.add_edge(START, "generate")
    graph.add_edge("generate", "reflect")
    graph.add_edge("reflect", END)
    return graph.compile()
