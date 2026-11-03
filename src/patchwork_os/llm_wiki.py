# SPDX-License-Identifier: Apache-2.0
"""Local Markdown graph helpers and a bounded Obsidian trace scan.

Provides a 3-layer CMDS LLM-Wiki
(``raw/``, ``wiki/``, ``rules/``, ``index.md``) using only standard UTF-8
Markdown, POSIX relative links, and Python's standard library:

1. ``audit_itar_and_obsidian_hygiene``:
   Reports listed local directory, file and text markers. Its legacy name does
   not indicate an ITAR, export-control, dependency or network-isolation audit.
2. ``normalize_wikilinks_to_markdown``:
   Converts ``[[Page]]`` / ``[[Page|Label]]`` wikilinks into standard CommonMark
   relative links ``[Label](path.md)`` that work in GitHub, VS Code, Neovim,
   CLI viewers, and LLM agents without Obsidian.
3. ``build_llm_wiki_graph``:
   Parses YAML frontmatter, resolves forward links, computes bidirectional
   backlinks, and detects orphan nodes or broken links deterministically.
4. ``query_llm_wiki``:
   Deterministic local search ranked by lexical match + backlink centrality.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REQUIRED_LAYERS: tuple[str, ...] = ("raw", "wiki", "rules")
OBSIDIAN_ARTIFACT_NAMES: tuple[str, ...] = (".obsidian", "obsidian.json", "workspace.json")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def parse_frontmatter(markdown_text: str) -> Tuple[Dict[str, str], str]:
    """Parse simple YAML frontmatter key-value pairs using pure stdlib."""
    match = FRONTMATTER_RE.match(markdown_text)
    if not match:
        return {}, markdown_text
    meta: Dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip().strip('"').strip("'")
    body = markdown_text[match.end():]
    return meta, body


def audit_itar_and_obsidian_hygiene(repo_or_hub_root: Path) -> Dict[str, Any]:
    """Scan local Obsidian markers; the legacy ITAR API name is deprecated.

    obsidian_traces_absent describes only the listed scan results. The legacy
    zero_obsidian_dependency key is a deprecated alias with the same limited
    meaning. Neither key assesses installed dependencies, ITAR or air gaps.
    """
    root = repo_or_hub_root.resolve()
    obsidian_dirs: List[str] = []
    canvas_files: List[str] = []
    obsidian_uri_hits: List[str] = []
    obsidian_prose_hits: List[str] = []

    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        if path.is_dir() and path.name.lower() == ".obsidian":
            obsidian_dirs.append(rel)
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() == ".canvas":
            canvas_files.append(rel)
        if path.suffix.lower() in {".md", ".json", ".toml", ".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if "obsidian://" in text.lower():
                obsidian_uri_hits.append(rel)
            if re.search(r"\bobsidian\b", text, re.IGNORECASE):
                obsidian_prose_hits.append(rel)

    passed = (
        len(obsidian_dirs) == 0
        and len(canvas_files) == 0
        and len(obsidian_uri_hits) == 0
        and len(obsidian_prose_hits) == 0
    )
    return {
        "root": str(root),
        "obsidian_traces_absent": passed,
        "zero_obsidian_dependency": passed,
        "deprecated_aliases": {"zero_obsidian_dependency": "obsidian_traces_absent"},
        "assessment_scope": "Listed local artifact and text markers only",
        "itar_assessment": "not_run",
        "airgap_assessment": "not_run",
        "obsidian_dirs": obsidian_dirs,
        "canvas_files": canvas_files,
        "obsidian_uri_hits": obsidian_uri_hits,
        "obsidian_prose_hits": obsidian_prose_hits,
    }


def normalize_wikilinks_to_markdown(
    markdown_text: str,
    slug_to_relpath: Optional[Dict[str, str]] = None,
) -> str:
    """Convert [[target|label]] wikilinks into standard CommonMark [label](target.md) links."""
    mapping = slug_to_relpath or {}

    def _replace(match: re.Match[str]) -> str:
        target_raw = match.group(1).strip()
        label = (match.group(2) or target_raw).strip()
        slug = target_raw.lower().replace(" ", "-")
        if not slug.endswith(".md"):
            rel_path = mapping.get(slug, f"{slug}.md")
        else:
            rel_path = mapping.get(slug[:-3], slug)
        return f"[{label}]({rel_path})"

    return WIKILINK_RE.sub(_replace, markdown_text)


def build_llm_wiki_graph(hub_root: Path) -> Dict[str, Any]:
    """Build a deterministic bidirectional link + frontmatter graph over a 3-layer LLM-Wiki hub."""
    hub_root = hub_root.resolve()
    missing_layers = [layer for layer in REQUIRED_LAYERS if not (hub_root / layer).is_dir()]
    has_index = (hub_root / "index.md").is_file()

    md_files = sorted(p for p in hub_root.rglob("*.md") if ".git" not in p.parts)
    nodes: Dict[str, Dict[str, Any]] = {}
    backlinks: Dict[str, List[str]] = {}
    broken_links: List[Dict[str, str]] = []

    for md_path in md_files:
        rel = md_path.relative_to(hub_root).as_posix()
        backlinks.setdefault(rel, [])

    for md_path in md_files:
        rel = md_path.relative_to(hub_root).as_posix()
        text = md_path.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(text)
        body_no_code = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
        body_no_code = re.sub(r"`[^`\n]+`", "", body_no_code)
        forward_links: List[str] = []

        for m in MD_LINK_RE.finditer(body_no_code):
            href = m.group(2).strip()
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            href_clean = href.split("#", 1)[0].strip()
            if not href_clean:
                continue
            target_path = (md_path.parent / href_clean).resolve()
            try:
                target_rel = target_path.relative_to(hub_root).as_posix()
            except ValueError:
                # Link points outside hub_root (e.g., repo root LICENSE); verify file exists
                if not target_path.exists():
                    broken_links.append({"source": rel, "target": href})
                continue
            if target_path.is_file():
                forward_links.append(target_rel)
                backlinks.setdefault(target_rel, [])
                if rel not in backlinks[target_rel]:
                    backlinks[target_rel].append(rel)
            else:
                broken_links.append({"source": rel, "target": href})

        nodes[rel] = {
            "path": rel,
            "title": meta.get("title") or md_path.stem,
            "layer": meta.get("layer") or (rel.split("/")[0] if "/" in rel else "hub"),
            "frontmatter": meta,
            "forward_links": forward_links,
        }

    for rel, node in nodes.items():
        node["backlinks"] = sorted(backlinks.get(rel, []))

    orphans = sorted(
        rel
        for rel, node in nodes.items()
        if rel != "index.md" and len(node["backlinks"]) == 0
    )

    return {
        "hub_root": str(hub_root),
        "has_index": has_index,
        "missing_layers": missing_layers,
        "node_count": len(nodes),
        "nodes": nodes,
        "broken_links": broken_links,
        "orphan_nodes": orphans,
        "valid": has_index and len(missing_layers) == 0 and len(broken_links) == 0,
    }


def query_llm_wiki(
    hub_root: Path,
    query: str,
    layer: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Search the pure-Markdown LLM-Wiki deterministically with backlink-boosted scoring."""
    graph = build_llm_wiki_graph(hub_root)
    tokens = [t.lower() for t in re.split(r"\W+", query) if t.strip()]
    results: List[Dict[str, Any]] = []

    for rel, node in graph["nodes"].items():
        if layer and node["layer"] != layer:
            continue
        full_text = (hub_root / rel).read_text(encoding="utf-8", errors="replace").lower()
        title_lower = str(node["title"]).lower()
        score = 0
        for tok in tokens:
            if tok in title_lower:
                score += 5
            score += full_text.count(tok)
        if score > 0:
            score += len(node["backlinks"])
            results.append(
                {
                    "path": rel,
                    "title": node["title"],
                    "layer": node["layer"],
                    "score": score,
                    "backlinks": node["backlinks"],
                    "forward_links": node["forward_links"],
                }
            )

    results.sort(key=lambda item: (-item["score"], item["path"]))
    return results[:limit]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Local Markdown graph and bounded Obsidian trace scan.")
    parser.add_argument("--hub-root", type=Path, required=True, help="Path to 3-layer knowledge hub directory")
    parser.add_argument("--audit-root", type=Path, help="Optional root to scan for listed local Obsidian markers")
    parser.add_argument("--query", default="", help="Optional search query across the LLM-Wiki")
    args = parser.parse_args(argv)

    audit_target = args.audit_root or args.hub_root
    hygiene = audit_itar_and_obsidian_hygiene(audit_target)
    graph = build_llm_wiki_graph(args.hub_root)
    hits = query_llm_wiki(args.hub_root, args.query) if args.query else []

    out = {
        "hygiene": hygiene,
        "graph_summary": {
            "valid": graph["valid"],
            "node_count": graph["node_count"],
            "missing_layers": graph["missing_layers"],
            "broken_links": graph["broken_links"],
            "orphan_nodes": graph["orphan_nodes"],
        },
        "query_hits": hits,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if (hygiene["obsidian_traces_absent"] and graph["valid"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
