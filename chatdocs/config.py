from pathlib import Path
from typing import Any, Dict, Union
import yaml

FILENAME = "chatdocs.yml"

def _get_config(path: Union[Path, str]) -> Dict[str, Any]:
    path = Path(path)
    if path.is_dir():
        path = path / FILENAME
    with open(path) as f:
        return yaml.safe_load(f)


def get_config() -> Dict[str, Any]:
    config = _get_config(Path(__file__).parent)
    return config
