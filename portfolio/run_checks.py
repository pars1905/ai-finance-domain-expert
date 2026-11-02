"""Run all seven project suites and regenerate offline sample reports."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECTS = [('01-financial-answer-evaluator', 'evaluate.py'),
            ('02-evidence-auditor', 'audit.py'),
            ('03-evaluation-release-gate', 'compare.py'),
            ('04-budget-variance-assistant', 'analyze.py'),
            ('05-cash-collection-workbench', 'prioritize.py'),
            ('06-supplier-proposal-assistant', 'compare_bids.py'),
            ('07-cited-financial-assistant', 'assistant.py')]

subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-v',
                '-p', 'test_business_tools.py'], cwd=ROOT, check=True)

for folder, script in PROJECTS:
    path = ROOT / folder
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-v'], cwd=path, check=True)
    args = [sys.executable, script, '--output', 'sample-report.json']
    if folder.startswith(('04-', '05-', '06-', '07-')):
        args += ['--markdown', 'sample-report.md']
    result = subprocess.run(args, cwd=path, check=True, capture_output=True, text=True)
    print(f'{folder}: sample report regenerated', flush=True)

subprocess.run([sys.executable, 'evaluate.py', '--output', 'evaluation-report.json'],
               cwd=ROOT / '07-cited-financial-assistant', check=True, capture_output=True, text=True)
print('07-cited-financial-assistant: development/holdout retrieval report regenerated', flush=True)
