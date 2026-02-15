# wtplan

**wtplan** は、Issue 番号を起点に複数リポジトリの Git worktree（workspace）をまとめて管理するツール。
Inventory（YAML）→ Plan → Apply の流れで、誤操作を防ぐ仕組みを組み込んでいる。
MCP（Model Context Protocol）の stdio サーバーとしても動作し、Tools/Prompts を提供する。

## インストール（uvx / 開発）

### uvx（GitHub からそのまま実行）

```bash
uvx --from git+https://github.com/<ORG>/<REPO>.git wtplan --help
```

### 開発（uv）

```bash
uv sync
uv run wtplan --help
```

## 使い方（CLI）

### 初期化

```bash
wtplan init --toolbox /workspace/toolbox
```

- `.wtplan.yml` がなければ生成（`default_policy` を含む雛形）
- `bare/` と `worktrees/` を作成

### workspace パスの取得（cd 補助に使える）

```bash
wtplan path <PRESET> <IID> --repo <ALIAS>
```

### 補完（bash）

```bash
eval "$(wtplan completion bash)"
```

### cd（シェル組み込みなので eval 前提）

```bash
eval "$(wtplan cd <PRESET> <IID> --repo <ALIAS>)"
```

## links_repo_root の上書きポリシー

- `--force-links` = **rsync -a 相当（delete なし）**
- `--delete-links` = **rsync -a --delete 相当（delete あり）**

`default_policy.links_repo_root.force/delete` は **全コマンド（plan / preset_add / preset_rm / init）で共通**して解釈する。

## MCP（stdio）

`wtplan` を引数なしで起動すると stdio の MCP サーバーとして待ち受ける。

```bash
wtplan
```

### 公開 Tools（v0.1）

- `init`
- `preset_add`（links の plan/apply のみ実装。git worktree は未実装）
- `preset_rm`（スタブ）
- `plan`（links の差分）
- `path`（参照専用）

### 公開 Prompts（v0.1）

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
