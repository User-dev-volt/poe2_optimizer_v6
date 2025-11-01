"""Quick script to run Story 1.6 parity tests and capture results."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/integration/test_pob_parity.py", "-v", "--tb=short"],
    capture_output=True,
    text=True,
    timeout=120
)

# Print last 100 lines to see results and any errors
lines = result.stdout.split('\n') + result.stderr.split('\n')
for line in lines[-100:]:
    if line.strip():
        print(line)

sys.exit(result.returncode)
