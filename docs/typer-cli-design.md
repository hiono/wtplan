# typer CLI Architecture Design

## Structure

```
wtplan (root Typer app)
├── init
├── plan
├── completion
├── preset (sub-Typer app)
│   ├── add <preset> <issue-iid> [--base] [--apply] [--force-links] [--delete-links]
│   ├── rm <preset> <issue-iid> [--force]
│   └── path <preset> <issue-iid>
├── repo (sub-Typer app)
│   ├── add <repo> <issue-iid> [--base] [--apply] [--force-links] [--delete-links]
│   ├── rm <repo> <issue-iid> [--force]
│   └── path <repo> <issue-iid>
├── cd (deprecated - redirects to preset cd)
└── path (deprecated - redirects to preset path)
```

## MCP Server Mode Detection

```python
# __main__.py
import sys
from .cli import app
from .mcp_server import mcp

if len(sys.argv) == 1:
    # No arguments → MCP server mode
    mcp.run()
else:
    # Has arguments → CLI mode
    app()
```

## Migration from argparse

| argparse | typer |
|----------|-------|
| subparsers.add_parser() | typer.Typer() |
| add_argument() | Function parameters with type hints |
| set_defaults(func=) | @app.command() decorator |
| argparse.Namespace | Function parameters |

## Shared Arguments Pattern

```python
# Common options for add commands
def add_options(
    base: Optional[str] = typer.Option(None, "--base", "-b"),
    apply: bool = typer.Option(False, "--apply", "-a"),
    force_links: bool = typer.Option(False, "--force-links"),
    delete_links: bool = typer.Option(False, "--delete-links"),
) -> AddOptions:
    return AddOptions(base, apply, force_links, delete_links)
```

## Deprecation Pattern

```python
@app.command()
def path(
    preset: str = typer.Argument(...),
    iid: int = typer.Argument(...),
    repo: Optional[str] = typer.Option(None),
):
    """[DEPRECATED] Use 'wtplan preset path' or 'wtplan repo path' instead."""
    console.print(
        "[yellow]Warning: 'wtplan path' is deprecated. "
        "Use 'wtplan preset path <preset> <iid>' or 'wtplan repo path <repo> <iid>'[/yellow]"
    )
    # Redirect to preset path for backward compatibility
    preset_path(preset=preset, iid=iid)
```
