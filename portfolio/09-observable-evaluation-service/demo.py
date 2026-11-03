"""Generate a synthetic telemetry report without an external API call."""
import argparse
import json
import tempfile
from pathlib import Path
from service import metrics, run_evaluation


def fake(payload, key, timeout):
    return 200, json.dumps({'status': 'completed', 'usage': {'input_tokens': 12, 'output_tokens': 7},
        'output': [{'type': 'message', 'content': [{'type': 'output_text',
        'text': 'Fictional ExampleCo revenue: 120 million USD.'}]}]}).encode()


def demo():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'telemetry.db'
        first = run_evaluation(path, 'What is fictional ExampleCo revenue?', 'mock-model',
                               'synthetic-key', transport=fake, daily_budget=2000, per_minute=1)
        second = run_evaluation(path, 'Second prompt', 'mock-model', 'synthetic-key',
                                transport=fake, daily_budget=2000, per_minute=1)
        observed = metrics(path)
        return {'scope': 'synthetic local transport; no live OpenAI request or model validation',
                'first': first, 'second': second, 'telemetry': observed,
                'limitations': ['Latency measures the injected transport call, not internet latency.',
                                'Rate and budget limits apply to this one local database, not a distributed deployment.',
                                'Failed attempts without reported usage consume a conservative budget estimate.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    report = demo()
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end='')
