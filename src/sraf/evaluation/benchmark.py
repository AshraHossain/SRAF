import csv
import json
from pathlib import Path

from sraf.core.engine import ReflectionEngine
from sraf.core.models import Policy
from sraf.core.providers import FixtureGenerator, FixtureJudge


def run(dataset: str, out: str) -> None:
    rows = []
    cases = json.loads(Path(dataset).read_text(encoding="utf-8"))
    for case in cases:
        for reflective in (False, True):
            policy = Policy(max_iterations=2 if reflective else 0)
            result = ReflectionEngine(FixtureJudge(), FixtureGenerator(), policy).run(case["prompt"], case["draft"], case["evidence"])
            rows.append({"case":case["id"], "framework":"core", "model":"fixture", "reflective":reflective,
                         "score":result.score, "iterations":result.metrics.iteration_count,
                         "cost":result.metrics.cost, "improvement_delta":result.metrics.improvement_delta,
                         "approved":result.approved, "error":result.score < policy.min_score,
                         "tool_call_success": "not_measured"})
    target = Path(out); target.mkdir(parents=True, exist_ok=True)
    (target/'metrics.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    with (target/'metrics.csv').open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    baseline=sum(r['score'] for r in rows if not r['reflective'])/(len(rows)/2)
    improved=sum(r['score'] for r in rows if r['reflective'])/(len(rows)/2)
    (target/'report.md').write_text(f'# Fixture benchmark\n\nBaseline: {baseline:.3f}; reflective: {improved:.3f}; delta: {improved-baseline:.3f}.\n\nSynthetic fixture only; not a real-world accuracy claim. Framework/model comparisons require paired provider-backed runs and human-labeled data.\n',encoding='utf-8')
if __name__ == '__main__':
    import sys
    run(sys.argv[1] if len(sys.argv)>1 else 'evaluation/dataset.json', sys.argv[2] if len(sys.argv)>2 else 'artifacts/benchmark')
