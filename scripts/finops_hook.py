#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""OEO SubagentStop hook: append one subagent's token usage to <project>/.oeo/finops.jsonl.

Local only (nothing leaves the machine) and opt-in by presence: it writes only when the
project already has a .oeo/ directory (created by `oeo route --log`). Disable with
OEO_FINOPS=off. The transcript format is internal to Claude Code, so parsing is
best-effort: unknown shapes are skipped and the hook never fails the session.
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oeo import append_jsonl, project_dir  # noqa: E402  (stdlib-only part of the CLI)

FIELDS = {"input_tokens": "input_tokens", "output_tokens": "output_tokens",
          "cache_read_input_tokens": "cache_read_tokens", "cache_creation_input_tokens": "cache_write_tokens"}


def usage_from_transcript(path):
    """Sum usage per unique assistant message id (one API response spans several lines)."""
    per_message, models = {}, set()
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = entry.get("message") if isinstance(entry, dict) else None
            if not isinstance(msg, dict) or not isinstance(msg.get("usage"), dict):
                continue
            key = msg.get("id") or entry.get("uuid") or f"line-{n}"
            prev = per_message.setdefault(key, {})
            for src, dst in FIELDS.items():
                val = msg["usage"].get(src)
                if isinstance(val, int):
                    prev[dst] = max(prev.get(dst, 0), val)  # streamed copies repeat or grow
            if msg.get("model"):
                models.add(msg["model"])
    totals = {dst: sum(m.get(dst, 0) for m in per_message.values()) for dst in FIELDS.values()}
    return totals, sorted(models), len(per_message)


def main():
    if os.environ.get("OEO_FINOPS", "").lower() in ("off", "0", "false"):
        return 0
    try:
        raw = sys.stdin.buffer.read() if hasattr(sys.stdin, "buffer") else sys.stdin.read().encode("utf-8")
        payload = json.loads(raw.decode("utf-8"))
        log_dir = project_dir(payload.get("cwd")) / ".oeo"
        transcript = payload.get("agent_transcript_path")
        if not log_dir.is_dir() or not transcript or not Path(transcript).is_file():
            return 0
        totals, models, responses = usage_from_transcript(transcript)
        record = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                  "session_id": payload.get("session_id"), "agent_type": payload.get("agent_type"),
                  "agent_id": payload.get("agent_id"), "models": models, "api_responses": responses,
                  **totals, "source": "best-effort transcript parse"}
        append_jsonl(log_dir / "finops.jsonl", record)
    except Exception:  # noqa: BLE001 - a logging hook must never break the session
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
