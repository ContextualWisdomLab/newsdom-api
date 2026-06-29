import subprocess
import json

out = subprocess.run(["python3", "-m", "pytest", "tests/test_dom_builder.py", "-k", "_coerce_page_number", "--cov=src/newsdom_api/dom_builder.py", "--cov-report=json"], capture_output=True, text=True)
with open("coverage.json", "r") as f:
    data = json.load(f)

lines = data['files']['src/newsdom_api/dom_builder.py']['executed_lines']
print(f"Executed lines: {sorted(lines)}")
missing = data['files']['src/newsdom_api/dom_builder.py']['missing_lines']
print(f"Missing lines: {sorted(missing)}")
