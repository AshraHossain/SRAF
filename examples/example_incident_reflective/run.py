from sraf.core.engine import ReflectionEngine
from sraf.core.models import Policy
from sraf.core.providers import FixtureJudge, FixtureGenerator
result = ReflectionEngine(FixtureJudge(), FixtureGenerator(), Policy(required_human_review=True)).run('Should we roll back?', "Initial draft", 'Alert: error rate elevated; no root cause confirmed', pending_actions=['rollback deployment'])
print(result)
