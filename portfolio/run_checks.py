"""Run all three standalone suites and regenerate their sample reports."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECTS = [('01-financial-answer-evaluator', 'evaluate.py'),
            ('02-evidence-auditor', 'audit.py'),
            ('03-evaluation-release-gate', 'compare.py')]

for folder, script in PROJECTS:
    path = ROOT / folder
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-v'], cwd=path, check=True)
    subprocess.run([sys.executable, script, '--output', 'sample-report.json'], cwd=path, check=True)
