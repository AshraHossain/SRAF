from sraf.core.engine import ReflectionEngine


def run_crew_with_review(topic: str, engine: ReflectionEngine, llm=None):
    from crewai import Agent, Crew, Process, Task
    kwargs = {"llm": llm} if llm is not None else {}
    researcher = Agent(role="Researcher", goal="Draft grounded research", backstory="Careful analyst", **kwargs)
    reviewer = Agent(role="Reviewer", goal="Find unsupported claims", backstory="Independent critic", **kwargs)
    draft = Task(description=f"Research {topic}; do not invent citations", expected_output="Short research note", agent=researcher)
    review = Task(description="Review preceding research for unsupported claims; do not approve actions", expected_output="Critique with evidence gaps", agent=reviewer, context=[draft])
    crew = Crew(agents=[researcher, reviewer], tasks=[draft, review], process=Process.sequential)
    crew.kickoff()
    candidate = str(draft.output.raw) if draft.output else ""
    feedback = str(review.output.raw) if review.output else ""
    return engine.run(topic + " Reviewer feedback: " + feedback, candidate)
