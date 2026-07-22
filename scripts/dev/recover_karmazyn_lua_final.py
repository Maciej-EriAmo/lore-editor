#!/usr/bin/env python3
"""Best-effort recovery from all session sources."""
import json
import re
from pathlib import Path

ROOT = Path(r"C:\Users\drwis\.grok\sessions")
OUT = Path(r"C:\Users\drwis\Karmazyn_lua")
SESSION = ROOT / r"C%3A%5CUsers%5Cdrwis%5Clore-editor\019f4bc5-98c8-7fe1-bff6-ab7f01e2de6b"


def basename_from_path(p: str) -> str | None:
    p = p.replace("\\\\", "\\")
    if "Karmazyn_lua" not in p:
        return None
    name = Path(p).name
    return name if name.endswith(".py") else None


def parse_chunk(content: str) -> dict[int, str]:
    if not isinstance(content, str) or content.startswith("Failed to read"):
        return {}
    lines: dict[int, str] = {}
    for ln in content.split("\n"):
        if re.match(r"^\.\.\. \d+ lines not shown \.\.\.", ln):
            continue
        sm = re.match(r"^\s*(\d+)\|(.*)$", ln)
        if sm:
            lines[int(sm.group(1))] = sm.group(2)
    return lines


def merge_lines(chunks: list[dict[int, str]]) -> str:
    merged: dict[int, str] = {}
    for ch in chunks:
        merged.update(ch)
    if not merged:
        return ""
    mx = max(merged)
    return "\n".join(merged.get(i, f"# RECOVERY_GAP line {i}") for i in range(1, mx + 1))


def ingest_pair(bn: str, content: str, files: dict[str, list]):
    ch = parse_chunk(content)
    if ch:
        files.setdefault(bn, []).append(ch)
    elif content and ('"""karmazyn_lua' in content[:100] or content.startswith("#!/usr/bin/env")):
        # full file without line numbers (recover1 style)
        if bn not in files or len(content) > sum(len(x) for x in files.get(bn, [{}])):
            files[bn] = [{"__full__": content}]


def stitch(files: dict[str, list]) -> str:
    chunks = files
    if chunks and "__full__" in chunks[0]:
        # prefer longest full snapshot
        return max(chunks[0].values()) if False else chunks[0]["__full__"]
    line_chunks = [c for c in chunks if isinstance(c, dict) and "__full__" not in c]
    full = next((c["__full__"] for c in chunks if isinstance(c, dict) and "__full__" in c), None)
    merged = merge_lines(line_chunks) if line_chunks else ""
    if full and len(full) > len(merged):
        return full
    return merged


def walk_json(obj, pending: dict, files: dict):
    if isinstance(obj, dict):
        if obj.get("type") == "assistant":
            for tc in obj.get("tool_calls") or []:
                if tc.get("name") == "Read":
                    args = tc.get("arguments")
                    if isinstance(args, str):
                        args = json.loads(args)
                    bn = basename_from_path(args.get("path", ""))
                    if bn:
                        pending[tc["id"]] = bn
        elif obj.get("type") == "tool_result":
            tid = obj.get("tool_call_id")
            if tid in pending:
                ingest_pair(pending.pop(tid), obj.get("content", ""), files)
        for v in obj.values():
            walk_json(v, pending, files)
    elif isinstance(obj, list):
        for x in obj:
            walk_json(x, pending, files)


def main():
    files: dict[str, list] = {}
    pending: dict = {}

    sources = list(SESSION.glob("*.jsonl"))
    sources += list(SESSION.glob("compaction_requests/*.json"))
    sources += list(SESSION.glob("recap_requests/*.json"))

    for src in sources:
        print(f"scan {src.name}")
        if src.suffix == ".jsonl":
            with open(src, encoding="utf-8") as f:
                for line in f:
                    try:
                        walk_json(json.loads(line), pending, files)
                    except json.JSONDecodeError:
                        pass
        else:
            try:
                walk_json(json.loads(src.read_text(encoding="utf-8")), pending, files)
            except Exception as e:
                print(f"  skip {e}")

    OUT.mkdir(parents=True, exist_ok=True)
    for bn in sorted(files):
        text = stitch(files[bn])
        gaps = text.count("RECOVERY_GAP")
        (OUT / bn).write_text(text, encoding="utf-8", newline="\n")
        print(f"  {bn}: {len(text)} bytes, {text.count(chr(10))+1} lines, gaps={gaps}")

    (OUT / "__init__.py").write_text(
        "from .lib import mount\nfrom .evaluator import Evaluator\n",
        encoding="utf-8",
        newline="\n",
    )
    print("done ->", OUT)


if __name__ == "__main__":
    main()