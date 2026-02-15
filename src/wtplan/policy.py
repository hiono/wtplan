from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LinkPolicy:
    type: str = "symlink"  # symlink|copy
    force: bool = False
    delete: bool = False


def effective_policy(inv: dict, *, cli_force: bool, cli_delete: bool) -> LinkPolicy:
    dp = (inv.get("default_policy") or {}).get("links_repo_root") or {}
    base = LinkPolicy(
        type=str(dp.get("type", "symlink")),
        force=bool(dp.get("force", False)),
        delete=bool(dp.get("delete", False)),
    )

    force = base.force
    delete = base.delete
    if cli_force:
        force = True
    if cli_delete:
        force = True
        delete = True

    return LinkPolicy(type=base.type, force=force, delete=delete)


def per_link_policy(item: dict, default: LinkPolicy) -> LinkPolicy:
    pol = item.get("policy")
    if pol is None:
        pol = {k: item.get(k) for k in ("force", "delete", "type") if k in item}
    if not pol:
        return default
    return LinkPolicy(
        type=str(pol.get("type", default.type)),
        force=bool(pol.get("force", default.force)),
        delete=bool(pol.get("delete", default.delete)),
    )
