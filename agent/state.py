from typing import TypedDict, List, Dict, Any, Optional

class DependencyState(TypedDict):
    project_path: str
    db_path: str
    dependency_files: List[str]
    dependencies: List[Dict[str, Any]]
    results: List[Dict[str, Any]]
    ctx: Optional[Any]