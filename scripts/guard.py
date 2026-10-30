#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""OEO PreToolUse guard: ask the human before destructive, publishing or secret-leaking actions.

Defense in depth, not a sandbox: pattern matching can be bypassed (aliases, scripts,
encodings). It never blocks outright; it turns risky calls into a confirmation prompt.
Disable with OEO_GUARD=off. Reads the hook JSON on stdin, prints a decision or nothing.
"""
import json
import os
import re
import sys

# (pattern, reason). Case-insensitive, matched against the full Bash command.
COMMAND_RULES = [
    (r"\brm\s+(-\w*\s+)*-\w*(r\w*f|f\w*r)\w*\s+(\S+\s+)*(/|~|\$HOME|\*|\.\.?)(/?\s|/?$|/\*)",
     "recursive force delete of a root, home, parent or wildcard path"),
    (r"\bgit\s+push\b.*(\s--force\b|\s-f\b|\s--force-with-lease\b|\s\+\S)", "force push rewrites remote history"),
    (r"\bgit\s+push\b.*(\s--tags\b|\s--mirror\b|\s--delete\b|\s:\S)", "pushes tags, mirrors or deletes remote refs"),
    (r"\bgit\s+(reset\s+--hard|clean\s+-\w*f|checkout\s+--\s+\.|restore\s+(--\S+\s+)*\.)", "discards local work"),
    (r"\bgit\s+branch\s+-D\b", "force-deletes a branch"),
    (r"\b(drop\s+(table|database|schema)|truncate\s+table)\b", "destructive SQL"),
    (r"\bdelete\s+from\s+\w+\s*(;|\"|'|$)", "DELETE without WHERE"),
    (r"\b(terraform|tofu)\s+(destroy|apply)\b|\bkubectl\s+delete\b|\bhelm\s+(uninstall|delete)\b",
     "changes or destroys infrastructure"),
    (r"\b(npm|pnpm|yarn)\s+publish\b|\btwine\s+upload\b|\bcargo\s+publish\b|\bgem\s+push\b|\bdocker\s+push\b"
     r"|\bgh\s+release\s+create\b|\bgh\s+repo\s+(delete|edit)\b", "publishes or changes something public"),
    (r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?)\b", "executes a remote script without review"),
    (r"\bchmod\s+(-R\s+)?0?777\b|\bmkfs(\.\w+)?\b|\bdd\s+[^|]*of=/dev/", "dangerous permission or disk operation"),
    (r"(\bcat|\bless|\bmore|\bhead|\btail)\s+[^|;&]*(\.env\b|id_rsa|id_ed25519|\.pem\b|credentials\b)",
     "prints a likely secrets file into the transcript"),
]

# (pattern, kind). Matched against content written by Write/Edit/MultiEdit.
SECRET_RULES = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key id"),
    (r"-----BEGIN (RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----", "private key"),
    (r"\bgh[pousr]_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b", "GitHub token"),
    (r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b", "Slack token"),
    (r"\bsk-ant-[A-Za-z0-9_-]{20,}\b", "Anthropic API key"),
    (r"\bsk-(proj-)?[A-Za-z0-9_-]{32,}\b", "OpenAI-style API key"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b", "Google API key"),
    (r"\b[rs]k_live_[0-9A-Za-z]{20,}\b", "Stripe live key"),
]


def check(payload):
    """Return a reason string if the tool call needs confirmation, else None."""
    tool = payload.get("tool_name", "")
    inp = payload.get("tool_input") or {}
    if tool == "Bash":
        cmd = inp.get("command", "")
        for pattern, reason in COMMAND_RULES:
            if re.search(pattern, cmd, re.IGNORECASE):
                return f"OEO guard: {reason}. Confirm this is intended and authorized."
        return None
    if tool in ("Write", "Edit", "MultiEdit"):
        parts = [inp.get("content", ""), inp.get("new_string", "")]
        parts += [e.get("new_string", "") for e in inp.get("edits", []) if isinstance(e, dict)]
        text = "\n".join(p for p in parts if isinstance(p, str))
        for pattern, kind in SECRET_RULES:
            if re.search(pattern, text):
                return (f"OEO guard: content for {inp.get('file_path', 'a file')} looks like it contains a "
                        f"{kind}. Secrets belong in a secret store or untracked env file.")
    return None


def main():
    if os.environ.get("OEO_GUARD", "").lower() in ("off", "0", "false"):
        return 0
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # fail open: a malformed event must not break the session
    reason = check(payload)
    if reason:
        json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                          "permissionDecisionReason": reason}}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
