
# wtplan

**wtplan** は、Issue 番号を起点に複数リポジトリの Git worktree（workspace）をまとめて管理するためのツールです。
Inventory（YAML）→ Plan → Apply の **ガードレール重視**の設計を採り、さらに **Model Context Protocol (MCP)** の **stdio サーバー**として Tools/Prompts を公開します。

> ⚠️ 本リポジトリの例・ログ・パス・ホスト名・組織名などはすべて匿名化してください（例: `<HOST>`）。

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

- `.wtplan.yml` が無ければ生成します（`default_policy` を含む雛形）。
- `bare/` と `worktrees/` を作成します。

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

`default_policy.links_repo_root.force/delete` は **全コマンド（plan / preset_add / preset_rm / init）で共通**に解釈されます。

## MCP（stdio）

`wtplan` を引数なしで起動すると stdio の MCP サーバーとして待ち受けます。

```bash
wtplan
```

### 公開 Tools（v0.1）

- `init`
- `preset_add`（links の plan/apply のみ実装。git worktree は未実装）
- `preset_rm`（スタブ）
- `plan`（links の差分）
- `path`（参照専用。MCP は B案: path のみ）

### 公開 Prompts（v0.1）

- `create_workspace_from_issue`
- `review_workspace_plan`
- `safe_remove_workspace`

## License

TBD
