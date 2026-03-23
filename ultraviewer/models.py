# ultraviewer/models.py
from typing import Optional
from pydantic import BaseModel

# --- Tabs ---
class TabCreate(BaseModel):
    name: str
    position: int = 0

class TabUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[int] = None

class TabResponse(BaseModel):
    id: int
    name: str
    position: int
    created_at: str

# --- Suites ---
class SuiteCreate(BaseModel):
    name: str
    folder_path: str
    scan_depth: int = 1
    position: int = 0

class ScriptConfig(BaseModel):
    interpreter: str = "python3"
    script_path: str = ""
    timeout_seconds: int = 30
    extra_args: list[dict] = []
    env_vars: list[dict] = []
    max_parallel: int = 1

class RenderingConfig(BaseModel):
    render_mode: str = "auto"
    config: dict = {}

class SuiteUpdate(BaseModel):
    name: Optional[str] = None
    folder_path: Optional[str] = None
    scan_depth: Optional[int] = None
    position: Optional[int] = None
    script: Optional[ScriptConfig] = None
    rendering: Optional[RenderingConfig] = None

class SuiteResponse(BaseModel):
    id: int
    tab_id: int
    name: str
    folder_path: str
    scan_depth: int
    position: int
    created_at: str
    script: Optional[ScriptConfig] = None
    rendering: Optional[RenderingConfig] = None

# --- Leaves ---
class LeafNode(BaseModel):
    name: str
    path: str

# --- Results ---
class RunResult(BaseModel):
    id: int
    suite_id: int
    leaf_name: str
    leaf_path: str
    result_json: dict
    status: str
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    run_at: str

class RunSummary(BaseModel):
    run_at: str
    total: int
    passed: int
    failed: int
    errors: int
