"""Test configuration for wtplan tests."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment with temporary inventory file."""
    # Create a temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    # Change to temp directory
    os.chdir(temp_dir)

    # Create a minimal inventory file
    inventory = {
        "version": "1",
        "primary_repo": "test-repo",
        "presets": {
            "default": {"primary_repo": "test-repo", "repos": ["test-repo"]},
            "test-preset": {"primary_repo": "test-repo", "repos": ["test-repo"]},
        },
        "links": [{"source": ".env", "target": ".env", "force": True}],
        "force_links": False,
        "delete_links": False,
    }

    # Write inventory file
    inventory_path = Path(temp_dir) / ".wtplan.yml"
    with open(inventory_path, "w") as f:
        yaml.dump(inventory, f)

    # Create required directories
    (Path(temp_dir) / "workspaces").mkdir(exist_ok=True)
    (Path(temp_dir) / "test-repo").mkdir(exist_ok=True)

    yield

    # Cleanup
    os.chdir(original_cwd)
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)
