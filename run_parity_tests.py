"""Quick script to run the GUI-truth parity tests (Story 1.6) and capture results.

The self-referential test_pob_parity.py / expected_stats.json pair was deprecated
(it validated the engine against its own prior output). test_gui_parity.py compares
against official PoB GUI baselines and is the single source of parity truth.
"""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/integration/test_gui_parity.py", "-v", "--tb=short"],
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
