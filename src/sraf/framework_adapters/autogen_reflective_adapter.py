from sraf.core.engine import ReflectionEngine


async def run_chat_with_judge(topic: str, model_client, engine: ReflectionEngine):
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.conditions import MaxMessageTermination
    from autogen_agentchat.teams import RoundRobinGroupChat
    author = AssistantAgent("author", model_client=model_client, system_message="Draft an answer. Do not execute actions.")
    judge = AssistantAgent("judge", model_client=model_client, system_message="Critique the author's answer, including unsupported claims. Never execute actions.")
    team = RoundRobinGroupChat([author, judge], termination_condition=MaxMessageTermination(2))
    run = await team.run(task=topic)
    draft = str(run.messages[1].content)
    critique = str(run.messages[2].content)
    return engine.run(topic + " Judge feedback: " + critique, draft)
