# wtplan

**wtplan** is a tool for managing Git worktrees (workspaces) across multiple repositories using an Issue number as the starting point.
It follows an Inventory → Plan → Apply workflow with built-in safeguards to prevent accidental operations.
It also runs as an MCP (Model Context Protocol) stdio server, providing Tools and Prompts.

## Installation (uvx / Development)

### uvx (Run directly from GitHub)

```bash
uvx --from git+https://github.com/hiono/wtplan.git wtplan --help
```

### Development (uv)

```bash
uv sync
uv run wtplan --help
```

## Usage (CLI)

### Initialization

```bash
wtplan init --toolbox /workspace/toolbox
```

- Creates `.wtplan.yml` if it doesn't exist (template including `default_policy`)
- Creates `bare/` and `worktrees/` directories

### Preset Mode Commands

Create and manage workspaces from a predefined preset configuration:

```bash
# Create workspace from preset
wtplan preset add <PRESET> <IID> [--apply] [--force-links] [--delete-links]

# Remove workspace
wtplan preset rm <PRESET> <IID>

# Get workspace path
wtplan preset path <PRESET> <IID> [--repo <ALIAS>]
```

### Single Repo Mode Commands

Create and manage workspaces from a single repository:

```bash
# Create workspace from single repo
wtplan repo add <REPO> <IID> [--apply] [--force-links] [--delete-links]

# Remove workspace
wtplan repo rm <REPO> <IID>

# Get workspace path
wtplan repo path <REPO> <IID>
```

### Completion (bash)

```bash
eval "$(wtplan completion bash)"
```

### cd (Requires shell integration via eval)

**Deprecated:** Use `wtplan preset path` or `wtplan repo path` instead.

```bash
eval "$(wtplan cd <PRESET> <IID> --repo <ALIAS>)"
```

## links_repo_root Override Policy

- `--force-links` = **rsync -a equivalent (without delete)**
- `--delete-links` = **rsync -a --delete equivalent (with delete)**

`default_policy.links_repo_root.force/delete` is **interpreted consistently across all commands** (plan / preset_add / preset_rm / init).

## MCP (stdio)

Launch `wtplan` with no arguments to start as an MCP stdio server.

```bash
wtplan
```

### Available Tools (v0.1)

**Preset Mode:**
- `preset_add` - Create workspace from preset + Issue IID (links plan/apply only, git worktree not implemented)
- `preset_rm` - Remove workspace from preset + Issue IID (stub)
- `preset_path` - Get workspace path from preset + Issue IID

**Single Repo Mode:**
- `repo_add` - Create workspace from single repo + Issue IID (links plan/apply only, git worktree not implemented)
- `repo_rm` - Remove workspace from single repo + Issue IID (stub)
- `repo_path` - Get workspace path from single repo + Issue IID

**Common:**
- `init` - Initialize inventory and workspace layout
- `plan` - Show differences between inventory and actual state

### Available Prompts (v0.1)

- `create_preset_workspace` - Create workspace from preset
- `create_repo_workspace` - Create workspace from single repo
- `review_workspace_plan` - Review plan and warn about destructive changes
- `safe_remove_preset` - Safely remove workspace from preset
- `safe_remove_repo` - Safely remove workspace from single repo

## License

MIT

## Acknowledgments

This tool is inspired by and adopts the repository management approach from:
- [tasteck/zenn](https://zenn.dev/tasteck/articles/50ecb1926a26a9)
- [tasuku43/gion](https://github.com/tasuku43/gion)

While following their workflow, this implementation incorporates MCP (Model Context Protocol) and configuration file setup for LLM Coding.
