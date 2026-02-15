# wtplan

**wtplan** is a tool for managing Git worktrees (workspaces) across multiple repositories using an Issue number as the starting point.
It follows an Inventory → Plan → Apply workflow with built-in safeguards to prevent accidental operations.
It also runs as an MCP (Model Context Protocol) stdio server, providing Tools and Prompts.

## Installation (uvx / Development)

### uvx (Run directly from GitHub)

```bash
uvx --from git+https://github.com/<ORG>/<REPO>.git wtplan --help
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

### Get Workspace Path (Useful for cd helper)

```bash
wtplan path <PRESET> <IID> --repo <ALIAS>
```

### Completion (bash)

```bash
eval "$(wtplan completion bash)"
```

### cd (Requires shell integration via eval)

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

- `init`
- `preset_add` (Only links plan/apply is implemented. Git worktree operations are not yet implemented)
- `preset_rm` (Stub)
- `plan` (Links diff)
- `path` (Read-only reference)

### Available Prompts (v0.1)

- `create_workspace_from_issue`
- `review_workspace_plan`
- `safe_remove_workspace`

## License

MIT

## Acknowledgments

This tool is inspired by and adopts the repository management approach from:
- [tasteck/zenn](https://zenn.dev/tasteck/articles/50ecb1926a26a9)
- [tasuku43/gion](https://github.com/tasuku43/gion)

While following their workflow, this implementation incorporates MCP (Model Context Protocol) and configuration file setup for LLM Coding.
