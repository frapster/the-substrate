"""
run_tests.py: run every demo's test suite, each in its own process.

Run it:

    python demos/run_tests.py

Standard library only. Each demo folder is self-contained and its tests import a local
module by bare name, so the suites are run in separate subprocesses (exactly as if you
ran each `python demos/<name>/test_*.py` by hand), with no shared import state, no package
plumbing, and the hyphenated folder names stay fine.

Exit code is 0 only if every suite passes.
"""

from __future__ import annotations

import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    test_files = sorted(glob.glob(os.path.join(HERE, "*", "test_*.py")))
    if not test_files:
        print("no test files found under demos/", file=sys.stderr)
        return 1

    failures: list[str] = []
    for path in test_files:
        rel = os.path.relpath(path, os.path.dirname(HERE))
        proc = subprocess.run([sys.executable, path], capture_output=True, text=True)
        # unittest writes its summary ("Ran N tests", "OK"/"FAILED") to stderr.
        summary = ""
        for line in (proc.stderr or "").splitlines():
            if line.startswith(("OK", "FAILED", "Ran ")):
                summary += line + " "
        mark = "ok  " if proc.returncode == 0 else "FAIL"
        print(f"  [{mark}] {rel}  {summary.strip()}")
        if proc.returncode != 0:
            failures.append(rel)
            if proc.stderr:
                print(proc.stderr.rstrip())

    print()
    if failures:
        print(f"✗ {len(failures)} suite(s) failed: {', '.join(failures)}")
        return 1
    print(f"✓ all {len(test_files)} demo suites passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
