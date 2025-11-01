"""Quick script to run Story 1.5 tests and capture results."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/integration/test_single_calculation.py", "-v", "--tb=no"],
    capture_output=True,
    text=True,
    timeout=60
)

# Print only lines with test results
for line in result.stdout.split('\n'):
    if 'PASSED' in line or 'FAILED' in line or 'passed' in line or 'failed' in line or '====' in line:
        print(line)

sys.exit(result.returncode)
