"""AI-run reference checks only. Never executes Unity, a model, or a user project."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

def main() -> int:
    root = Path(__file__).resolve().parent
    env = os.environ.copy()
    env['ASHFALL_HARNESS_ROOT'] = str(root / 'harness')
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    cases = [(root / 'harness', 'tests'), (root / 'harness', 'labs'),
             (root / 'expansion_tools', 'tests'), (root / 'game_tools', '.')]
    for work, tests in cases:
        print(f'\nReference check: {work.name} / {tests}', flush=True)
        try:
            result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', tests, '-v'],
                                    cwd=work, env=env, check=False, timeout=180)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f'Reference check could not finish: {exc}', file=sys.stderr)
            return 2
        if result.returncode != 0:
            print('Reference checks failed. No game success is inferred.', file=sys.stderr)
            return result.returncode if 0 < result.returncode < 256 else 1
    print('Reference checks passed; Unity, live model calls, and device tests were not run.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
