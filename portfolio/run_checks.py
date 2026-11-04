"""Run all twelve project suites and regenerate local sample reports."""
import argparse
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
            ('07-cited-financial-assistant', 'assistant.py'),
            ('08-finance-review-api', 'demo.py'),
            ('09-observable-evaluation-service', 'demo.py'),
            ('10-budget-exception-classifier', 'classify.py'),
            ('11-financial-forecast-benchmark', 'forecast.py'),
            ('12-financial-reasoning-experiment', 'experiment.py')]

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, help='Write generated reports outside the checkout')
args = parser.parse_args()
output_root = args.output_dir.resolve() if args.output_dir else ROOT

subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-v',
                '-p', 'test_*.py'], cwd=ROOT, check=True)

for folder, script in PROJECTS:
    path = ROOT / folder
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-v'], cwd=path, check=True)
    destination = output_root / folder
    destination.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, script, '--output', str(destination / 'sample-report.json')]
    if folder.startswith(('04-', '05-', '06-', '07-', '08-')):
        args += ['--markdown', str(destination / 'sample-report.md')]
    result = subprocess.run(args, cwd=path, check=True, capture_output=True, text=True)
    print(f'{folder}: sample report regenerated', flush=True)

subprocess.run([sys.executable, 'evaluate.py', '--output',
                str(output_root / '07-cited-financial-assistant' / 'evaluation-report.json')],
               cwd=ROOT / '07-cited-financial-assistant', check=True, capture_output=True, text=True)
print('07-cited-financial-assistant: development/holdout retrieval report regenerated', flush=True)
