from sraf.core.engine import ReflectionEngine
from sraf.core.models import Policy
from sraf.core.providers import FixtureJudge, FixtureGenerator
result = ReflectionEngine(FixtureJudge(), FixtureGenerator(), Policy(required_human_review=True)).run('What is the account opportunity?', "Initial draft", 'CRM: renewal due next quarter', pending_actions=[])
print(result)
