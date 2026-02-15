from pathlib import Path

from wtplan.core import ensure_inventory
from wtplan.inventory import load_inventory


def test_ensure_inventory(tmp_path: Path):
    cwd = tmp_path / "x"
    cwd.mkdir()
    ensure_inventory(cwd)
    inv = load_inventory(cwd / ".wtplan.yml")
    assert inv["version"] == 1
    assert "default_policy" in inv
