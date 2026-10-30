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
import shlex
import sys

# git with optional global options before the subcommand (git -C dir / -c k=v / --no-pager ...).
GIT = r"\bgit\b(?:\s+(?:-[Cc]\s+\S+|--?[\w.=/-]+))*\s+"

# (pattern, reason, applies_to_git_commands). Case-insensitive unless the pattern says (?-i:...).
# SQL rules skip git commands so commit messages such as "delete from cache" do not trigger them.
COMMAND_RULES = [
    (GIT + r"push\b.*(\s--force(-with-lease)?\b|\s-[a-zA-Z]*f[a-zA-Z]*\b|\s\+\S)", "force push rewrites remote history", True),
    (GIT + r"push\b.*(\s--tags\b|\s--mirror\b|\s--delete\b|\s:\S)", "pushes tags, mirrors or deletes remote refs", True),
    (GIT + r"(reset\s+(.*\s)?--hard\b|checkout\s+(--\s+)?\.(\s|$)|restore\s+(?!.*--staged)(.*\s)?\.(\s|$))",
     "discards local work", True),
    (GIT + r"clean\b(.*\s)?(-\w*f\w*|--force)\b", "deletes untracked files", True),
    (GIT + r"branch\s+(.*\s)?((?-i:-D)|--delete\s+--force|--force\s+--delete|-d\s+-f|-f\s+-d)(\s|$)",
     "force-deletes a branch", True),
    (r"\b(drop\s+(table|database|schema)|truncate\s+table)\b", "destructive SQL", False),
    (r"\bdelete\s+from\s+[\w.\"`\[\]]+\s*(;|\"|'|$)", "DELETE without WHERE", False),
    (r"\b(terraform|tofu)\s+(destroy|apply)\b|\bkubectl\s+delete\b|\bhelm\s+(uninstall|delete)\b",
     "changes or destroys infrastructure", True),
    (r"^(?!.*--dry-run\b).*(\b(npm|pnpm|yarn)\s+publish\b|\btwine\s+upload\b|\bcargo\s+publish\b|\bgem\s+push\b"
     r"|\bdocker\s+push\b|\bgh\s+release\s+create\b|\bgh\s+repo\s+(delete|edit)\b)", "publishes or changes something public", True),
    (r"\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?)\b", "executes a remote script without review", True),
    (r"\bchmod\s+(-R\s+)?0?777\b|\bmkfs(\.\w+)?\b|\bdd\s+[^|]*of=/dev/", "dangerous permission or disk operation", True),
    (r"(\bcat|\bless|\bmore|\bhead|\btail)\s+[^|;&]*"
     r"(\.env(?!\.(example|sample|template|dist))\b|id_rsa|id_ed25519|\.pem\b|credentials(?!\.md\b)\b)",
     "prints a likely secrets file into the transcript", True),
]

# rm targets that make a recursive force delete catastrophic.
DANGEROUS_RM_TARGETS = {"/", "/*", "~", "~/", "~/*", "$HOME", "$HOME/", "$HOME/*", "${HOME}", "${HOME}/",
                        "${HOME}/*", "*", ".", "./", "./*", ".*", "..", "../", "../*"}
TOP_LEVEL_DIR = re.compile(r"^/[^/\s]+/?\*?$")  # /usr, /etc/, /home/* ...

# (pattern, kind). Matched against content written by Write/Edit/MultiEdit.
SECRET_RULES = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key id"),
    (r"-----BEGIN (RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----|-----BEGIN PGP PRIVATE KEY BLOCK-----",
     "private key"),
    (r"\bgh[pousr]_[A-Za-z0-9]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b", "GitHub token"),
    (r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b", "Slack token"),
    (r"\bsk-ant-[A-Za-z0-9_-]{20,}\b", "Anthropic API key"),
    (r"\bsk-(proj-)?[A-Za-z0-9_-]{32,}\b", "OpenAI-style API key"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b", "Google API key"),
    (r"\b[rs]k_live_[0-9A-Za-z]{20,}\b", "Stripe live key"),
]


def dangerous_rm(cmd, depth=0):
    """True if any `rm` in the command is recursive + forced and targets a root/home/parent/wildcard
    or a top-level directory. Quoted sub-commands (bash -c '...', ssh host "...") are checked too."""
    for segment in re.split(r"[;&|()\n]+|\$\(|`", cmd):
        try:
            words = shlex.split(segment, posix=True)
        except ValueError:
            words = segment.split()
        if depth < 3 and any(dangerous_rm(w, depth + 1) for w in words if " " in w.strip()):
            return True
        for i, word in enumerate(words):
            if os.path.basename(word).lower() != "rm":  # case-insensitive filesystems run RM too
                continue
            recursive = force = False
            targets = []
            for arg in words[i + 1:]:
                low = arg.lower()
                if low == "--recursive":
                    recursive = True
                elif low == "--force":
                    force = True
                elif arg.startswith("-") and not arg.startswith("--") and len(arg) > 1:
                    recursive |= "r" in low
                    force |= "f" in low
                elif not arg.startswith("--"):
                    targets.append(arg)
            if recursive and force and any(t in DANGEROUS_RM_TARGETS or TOP_LEVEL_DIR.match(t) for t in targets):
                return True
    return False


def check(payload):
    """Return a reason string if the tool call needs confirmation, else None."""
    if not isinstance(payload, dict):
        return None
    tool, inp = payload.get("tool_name"), payload.get("tool_input")
    if not isinstance(inp, dict):
        return None
    if tool == "Bash":
        cmd = inp.get("command")
        if not isinstance(cmd, str):
            return None
        cmd = cmd.replace("\\\n", " ")  # join backslash-continued lines
        if dangerous_rm(cmd):
            return "OEO guard: recursive force delete of a root, home, parent or wildcard path. Confirm this is intended."
        is_git = re.match(r"\s*git\b", cmd) is not None
        for pattern, reason, applies_to_git in COMMAND_RULES:
            if (applies_to_git or not is_git) and re.search(pattern, cmd, re.IGNORECASE):
                return f"OEO guard: {reason}. Confirm this is intended and authorized."
        return None
    if tool in ("Write", "Edit", "MultiEdit"):
        edits = inp.get("edits") if isinstance(inp.get("edits"), list) else []
        parts = [inp.get("content"), inp.get("new_string")] + [e.get("new_string") for e in edits if isinstance(e, dict)]
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
        raw = sys.stdin.buffer.read() if hasattr(sys.stdin, "buffer") else sys.stdin.read().encode("utf-8")
        reason = check(json.loads(raw.decode("utf-8")))
    except Exception:  # noqa: BLE001 - fail open: a malformed event must not break the session
        return 0
    if reason:
        json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                          "permissionDecisionReason": reason}}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
