python -m pip install -e ".[dev]"
pytest -q
sraf --policy policies/default.json
python -m sraf.evaluation.benchmark
