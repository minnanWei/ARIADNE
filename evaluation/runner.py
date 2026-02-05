from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass

@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool
    runtime_s: float

def run_python(code: str, input_str: str, timeout_s: float) -> RunResult:
    start = time.time()
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        completed = subprocess.run(
            [sys.executable, "-u", tmp_path],
            input=input_str,
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
        runtime_s = time.time() - start
        return RunResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            timed_out=False,
            runtime_s=runtime_s,
        )
    except subprocess.TimeoutExpired as exc:
        runtime_s = time.time() - start
        return RunResult(
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            exit_code=-1,
            timed_out=True,
            runtime_s=runtime_s,
        )
