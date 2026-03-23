import os
import json
import pytest
from ultraviewer.runner import run_script

@pytest.mark.asyncio
async def test_run_script_success(tmp_path):
    script = tmp_path / "test.sh"
    script.write_text('#!/bin/bash\necho \'{"status": "pass", "name": "test"}\'')
    script.chmod(0o755)
    result = await run_script(interpreter="bash", script_path=str(script), leaf_path=str(tmp_path), extra_args=[], env_vars=[], timeout=10)
    assert result["status"] == "success"
    assert result["result"]["status"] == "pass"

@pytest.mark.asyncio
async def test_run_script_timeout(tmp_path):
    script = tmp_path / "slow.sh"
    script.write_text('#!/bin/bash\nsleep 10\necho "{}"')
    script.chmod(0o755)
    result = await run_script(interpreter="bash", script_path=str(script), leaf_path=str(tmp_path), extra_args=[], env_vars=[], timeout=1)
    assert result["status"] == "timeout"

@pytest.mark.asyncio
async def test_run_script_nonzero_exit(tmp_path):
    script = tmp_path / "fail.sh"
    script.write_text('#!/bin/bash\necho "something went wrong" >&2\nexit 1')
    script.chmod(0o755)
    result = await run_script(interpreter="bash", script_path=str(script), leaf_path=str(tmp_path), extra_args=[], env_vars=[], timeout=10)
    assert result["status"] == "error"
    assert "something went wrong" in result["error_message"]

@pytest.mark.asyncio
async def test_run_script_invalid_json(tmp_path):
    script = tmp_path / "bad.sh"
    script.write_text('#!/bin/bash\necho "not json"')
    script.chmod(0o755)
    result = await run_script(interpreter="bash", script_path=str(script), leaf_path=str(tmp_path), extra_args=[], env_vars=[], timeout=10)
    assert result["status"] == "error"
    assert "not json" in result.get("raw_stdout", "") or "JSON" in result.get("error_message", "")

@pytest.mark.asyncio
async def test_run_script_with_extra_args(tmp_path):
    script = tmp_path / "args.sh"
    script.write_text('#!/bin/bash\necho "{\\\"args\\\": \\\"$@\\\"}"')
    script.chmod(0o755)
    result = await run_script(interpreter="bash", script_path=str(script), leaf_path=str(tmp_path), extra_args=[{"key": "--golden", "value": "/data/golden"}], env_vars=[], timeout=10)
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_run_script_with_env_vars(tmp_path):
    script = tmp_path / "env.sh"
    script.write_text('#!/bin/bash\necho "{\\\"module\\\": \\\"$MODULE_NAME\\\"}"')
    script.chmod(0o755)
    result = await run_script(interpreter="bash", script_path=str(script), leaf_path=str(tmp_path), extra_args=[], env_vars=[{"key": "MODULE_NAME", "value": "login"}], timeout=10)
    assert result["status"] == "success"
    assert result["result"]["module"] == "login"
