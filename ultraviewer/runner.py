import asyncio
import json
import os
import time

async def run_script(
    interpreter: str,
    script_path: str,
    leaf_path: str,
    extra_args: list[dict],
    env_vars: list[dict],
    timeout: int,
) -> dict:
    """Execute a script against a leaf folder and return the result."""
    cmd = [interpreter, script_path, leaf_path]
    for arg in extra_args:
        cmd.append(arg["key"])
        if arg.get("value"):
            cmd.append(arg["value"])

    env = os.environ.copy()
    for var in env_vars:
        env[var["key"]] = var["value"]

    start = time.monotonic()

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            duration_ms = int((time.monotonic() - start) * 1000)
            return {"status": "timeout", "error_message": f"Timed out after {timeout}s", "duration_ms": duration_ms, "result": {}}

        duration_ms = int((time.monotonic() - start) * 1000)
        stdout_text = stdout.decode("utf-8", errors="replace").strip()
        stderr_text = stderr.decode("utf-8", errors="replace").strip()

        if proc.returncode != 0:
            return {"status": "error", "error_message": stderr_text or f"Exit code {proc.returncode}", "raw_stdout": stdout_text, "duration_ms": duration_ms, "result": {}}

        try:
            parsed = json.loads(stdout_text)
        except json.JSONDecodeError:
            return {"status": "error", "error_message": "Invalid JSON output", "raw_stdout": stdout_text, "duration_ms": duration_ms, "result": {}}

        return {"status": "success", "result": parsed, "duration_ms": duration_ms}

    except FileNotFoundError:
        return {"status": "error", "error_message": f"Script not found: {script_path}", "duration_ms": 0, "result": {}}
