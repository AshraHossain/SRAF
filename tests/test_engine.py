import pytest

from sraf.core.engine import ReflectionEngine
from sraf.core.models import Policy
from sraf.core.providers import FixtureGenerator, FixtureJudge


def engine(**kwargs):
    return ReflectionEngine(FixtureJudge(), FixtureGenerator(), Policy(**kwargs))

def test_reflects_and_logs():
    events=[]
    e=ReflectionEngine(FixtureJudge(), FixtureGenerator(), Policy(), events.append)
    result=e.run('task','draft','evidence')
    assert result.approved and result.metrics.iteration_count == 1
    assert result.metrics.improvement_delta > 0 and len(events)==2

def test_no_evidence_does_not_pass():
    assert not engine(max_iterations=0).run('task','draft').approved

def test_action_requires_approval():
    r=engine(required_human_review=True).run('task','draft','evidence',pending_actions=['deploy'])
    assert not r.approved and r.metrics.stop_reason == 'human_review_required'

def test_tool_blocked():
    with pytest.raises(ValueError):
        engine(forbidden_tools=('shell',)).run('task','draft',tools=('shell',))

def test_cost_ceiling():
    class Expensive:
        def generate(self,*args): return 'x', 1.0
    r=ReflectionEngine(FixtureJudge(), Expensive(), Policy(max_cost=0.1)).run('task','draft','evidence')
    assert r.metrics.stop_reason=='cost_ceiling' and not r.approved
