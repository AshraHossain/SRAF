import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .core.engine import ReflectionEngine
from .core.models import Policy
from .core.providers import FixtureGenerator, FixtureJudge
from .observability.store import JSONLStore


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="policies/default.json")
    parser.add_argument("--prompt", default="What does the incident report say?")
    parser.add_argument("--draft", default="Unverified draft")
    parser.add_argument("--evidence", default="Report: service is degraded")
    parser.add_argument("--trace", default="artifacts/trace.jsonl")
    args = parser.parse_args()
    policy = Policy(**json.loads(Path(args.policy).read_text(encoding="utf-8")))
    result = ReflectionEngine(FixtureJudge(), FixtureGenerator(), policy, JSONLStore(args.trace)).run(args.prompt, args.draft, args.evidence)
    print(json.dumps(asdict(result), indent=2))
if __name__ == "__main__":
    main()
