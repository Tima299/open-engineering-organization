# SPDX-License-Identifier: Apache-2.0
"""Deterministic checks behind OEO skills (stdlib only).

- engagement ids and `.oeo/<engagement>/` memory layout
- `status`: cross-engagement brief data for oeo:chief-of-staff
- `copy_lint`: the oeo:launch copy gate patterns
- `ledger_check`: the oeo:research finding-ledger rules
"""
import datetime as dt
import json
import re
from pathlib import Path

STATUS_WORDS = ("backlog", "todo", "in_progress", "in_review", "blocked", "done", "cancelled")


# --------------------------------------------------------------------------- engagements
def slugify(text, limit=40):
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return slug[:limit].rstrip("-") or "engagement"


def engagement_id(summary, explicit=None, today=None):
    """`--engagement` wins; else <YYYYMMDD>-<slug of summary>. Re-triage of the same request on
    the same day therefore lands in the same folder."""
    if explicit:
        return slugify(explicit, 60)
    day = (today or dt.date.today()).strftime("%Y%m%d")
    return f"{day}-{slugify(summary)}"


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


# --------------------------------------------------------------------------- markdown tables
def md_tables(text):
    """Yield (header_cells, rows) for each pipe table in a markdown text."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = [c.strip().lower() for c in lines[i].strip().strip("|").split("|")]
            rows, i = [], i + 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            yield header, rows
        else:
            i += 1


def column(header, *names):
    """Index of the first header equal to a name, else the first header containing one."""
    for n in names:
        if n in header:
            return header.index(n)
    for n in names:
        for idx, h in enumerate(header):
            if n in h:
                return idx
    return None


# --------------------------------------------------------------------------- status
def _plan_tasks(path):
    counts = {w: 0 for w in STATUS_WORDS}
    blocked, waiting = [], []
    if not path.exists():
        return None, blocked, waiting
    for header, rows in md_tables(path.read_text(encoding="utf-8")):
        s_col, id_col = column(header, "status"), column(header, "id", "task")
        if s_col is None:
            continue
        for r in rows:
            status = r[s_col].strip("` ").lower() if s_col < len(r) else ""
            word = next((w for w in STATUS_WORDS if status.startswith(w)), None)
            if not word:
                continue
            counts[word] += 1
            label = r[id_col] if id_col is not None and id_col < len(r) else "task"
            if word == "blocked":
                blocked.append(f"{label}: {r[s_col]}")
            if word == "in_review":
                waiting.append(f"{label}: waiting on a human")
    return counts, blocked, waiting


def _gates(path):
    result = {}
    if not path.exists():
        return result
    for header, rows in md_tables(path.read_text(encoding="utf-8")):
        g_col, r_col = column(header, "gate"), column(header, "result", "verdict", "pass/fail")
        if g_col is None or r_col is None:
            continue
        for r in rows:
            if max(g_col, r_col) < len(r):
                verdict = r[r_col].upper()
                result[r[g_col].strip("` ")] = ("FAIL" if "FAIL" in verdict else "N/A" if "N/A" in verdict
                                                 else "NOT RUN" if "NOT RUN" in verdict else
                                                 "PASS" if "PASS" in verdict else verdict or "?")
    return result


def _due_decisions(path, today):
    due = []
    if not path.exists():
        return due
    for header, rows in md_tables(path.read_text(encoding="utf-8")):
        rb, dc = column(header, "review_by", "review by"), column(header, "decision")
        if rb is None:
            continue
        for r in rows:
            m = re.search(r"\d{4}-\d{2}-\d{2}", r[rb]) if rb < len(r) else None
            try:
                when = dt.date.fromisoformat(m.group(0)) if m else None
            except ValueError:  # malformed date in a hand-edited log: skip the row, keep the brief
                continue
            if when and when <= today:
                due.append(f"review due {m.group(0)}: {r[dc] if dc is not None and dc < len(r) else r[0]}")
    return due


def status(base, today=None):
    """Brief data across engagements, from `.oeo/` files only (no model judgement)."""
    base, today = Path(base), today or dt.date.today()
    plans = read_jsonl(base / "activation-log.jsonl")
    usage = read_jsonl(base / "finops.jsonl")
    sessions = {}
    for p in (base / "sessions").glob("*.json") if (base / "sessions").is_dir() else []:
        try:
            snap = json.loads(p.read_text(encoding="utf-8"))
            sessions[snap.get("session_id")] = snap
        except (json.JSONDecodeError, OSError):
            continue
    latest = {}
    for p in plans:
        latest[p.get("engagement") or p.get("session") or "default"] = p
    engagements, needs_you, blocked_all = [], [], []
    for eid, plan in latest.items():
        folder = base / eid
        counts, blocked, waiting = _plan_tasks(folder / "plan.md")
        gates = _gates(folder / "verification.md")
        sess = {p.get("session") for p in plans if (p.get("engagement") or p.get("session") or "default") == eid} - {None}
        spent = sum(u.get("input_tokens", 0) + u.get("output_tokens", 0) + u.get("cache_write_tokens", 0)
                    for u in usage if u.get("session_id") in sess)
        main = sum(s.get("total_tokens", 0) for sid, s in sessions.items() if sid in sess)
        failing = [g for g, v in gates.items() if v in ("FAIL", "NOT RUN")]
        engagements.append({
            "engagement": eid, "summary": plan.get("summary"), "class": plan.get("class"),
            "last_activity": (plan.get("ts") or "")[:10],
            "tasks": counts, "gates": gates, "failing_gates": failing,
            "subagent_tokens": spent, "main_session_tokens": main,
            "budget_tokens": plan.get("budget_tokens", 0),
        })
        needs_you += [f"{eid}: {w}" for w in waiting]
        blocked_all += [f"{eid}: {b}" for b in blocked]
    due = _due_decisions(base / "decisions.md", today)
    needs_you += due
    if any(e["failing_gates"] for e in engagements):
        e = next(e for e in engagements if e["failing_gates"])
        nxt = f"{e['engagement']}: resolve gate {e['failing_gates'][0]}"
    elif needs_you:
        nxt = needs_you[0]
    elif blocked_all:
        nxt = f"unblock {blocked_all[0]}"
    else:
        nxt = "nothing waiting on you"
    over = [e["engagement"] for e in engagements
            if e["budget_tokens"] and e["subagent_tokens"] > 0.8 * e["budget_tokens"]]
    return {"needs_you": needs_you, "blocked": blocked_all, "engagements": engagements,
            "over_80_percent_budget": over, "next_action": nxt}


def format_status(s):
    def sec(title, items):
        shown = items[:5] + ([f"... and {len(items) - 5} more"] if len(items) > 5 else [])
        return [f"{title}:"] + ([f"  - {i}" for i in shown] or ["  - none"])
    out = sec("Needs you", s["needs_you"]) + sec("Blocked", s["blocked"])
    lines = []
    for e in s["engagements"]:
        t = e["tasks"]
        tasks = f"tasks {t['done']}/{sum(v for k, v in t.items() if k != 'cancelled')} done" if t else "no plan"
        gates = (f"gates {sum(v == 'PASS' for v in e['gates'].values())} pass"
                 + (f", {len(e['failing_gates'])} failing" if e["failing_gates"] else "")) if e["gates"] else "no gates yet"
        lines.append(f"{e['engagement']}: class {e['class']} · {tasks} · {gates} · last {e['last_activity']}")
    out += sec("Status", lines)
    budget = [f"{e['engagement']}: subagents {e['subagent_tokens']:,} + main {e['main_session_tokens']:,} "
              f"of {e['budget_tokens']:,} subagent budget" for e in s["engagements"]]
    out += sec("Budget", budget + [f"over 80%: {x}" for x in s["over_80_percent_budget"]])
    out.append(f"One next action: {s['next_action']}")
    return "\n".join(out)


# --------------------------------------------------------------------------- copy lint
COPY_RULES = [
    ("must-fix", "placeholder or filler text", re.compile(r"lorem ipsum|\bTBD\b|\bTODO\b|\[insert|\bplaceholder\b", re.I)),
    ("must-fix", "unfilled template slot", re.compile(r"\[[A-Z][A-Z0-9 _/-]{3,}\]|\{\{[^}]+\}\}|<[A-Z][A-Z0-9 _-]{3,}>")),
    ("must-fix", "testimonial or customer claim without a source",
     re.compile(r"(trusted by|loved by|used by|chosen by)\s+(over\s+|more than\s+)?[\d,.]+\+?\s*"
                r"(k|m|thousand|million|billion)?\s*(teams|users|developers|companies|customers|people)", re.I)),
    ("must-fix", "named customers, ratings or attributed quotes need a cited source",
     re.compile(r"\b(?i:used|trusted|loved|chosen) by [A-Z][\w&.-]+(,\s*[A-Z][\w&.-]+)+|\b\d(\.\d)?\s*(stars?|/\s*5)\b|"
                r"[\u2014\u2013-]{1,2}\s*[A-Z][a-z]+ [A-Z][a-z]+,\s*(CEO|CTO|VP|Head|Founder|Director|Engineer)")),
    ("should-fix", "stock opener or hype word",
     re.compile(r"in today'?s (fast-paced|digital)|\bunlock\b|\bsupercharge|\bseamless(ly)?\b|game[- ]chang|"
                r"\brevolutioni[sz]|\bcutting[- ]edge\b|\bnext[- ]gen\b|\bworld[- ]class\b|\bleverage\b|\bempower", re.I)),
    ("should-fix", "contrast reveal (\"not X. It's Y\")",
     re.compile(r"\b(it'?s|it is|this is|we'?re|we are)\s+not\s+(just\s+)?[^.!?]{1,60}[.!?]\s+(it'?s|it is|this is|we'?re|we are)\b", re.I)),
    ("should-fix", "stacked negation list", re.compile(r"\bno\s+\w+[^.!?]{0,30}[.!?]\s+no\s+\w+[^.!?]{0,30}[.!?]\s+no\s+\w+", re.I)),
    ("should-fix", "number or percentage without a source on the line",
     re.compile(r"(?<![\w.])(\d+(\.\d+)?\s?%|\d+x\s+(faster|more|better)|\d{2,}[,\d]*\+)", re.I)),
    ("should-fix", "vague call to action", re.compile(r"^\W*(learn more|click here|read more)\W*$", re.I)),
    ("polish", "intensifier", re.compile(r"\b(very|truly|incredibly|extremely|really|super)\s+\w+", re.I)),
]
SHORT_LINE = 90  # em dashes are flagged only in short-form copy (headlines, buttons, posts)
SOURCE_MARKER = re.compile(r"\[\^|\]\(|\bsource\b|\bper\b|\bmeasured\b", re.I)
NUMBER_RULE = "number or percentage without a source on the line"


def copy_lint(text):
    findings = []
    in_code = False
    for n, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code or not line.strip():
            continue
        line = line.replace("\u2019", "'").replace("\u2018", "'")  # curly apostrophes
        for severity, what, rx in COPY_RULES:
            m = rx.search(line)
            if m and not (what == NUMBER_RULE and SOURCE_MARKER.search(line)):
                findings.append({"line": n, "severity": severity, "rule": what, "text": m.group(0)})
        if "—" in line and len(line.strip()) <= SHORT_LINE:
            findings.append({"line": n, "severity": "should-fix", "rule": "em dash in short-form copy", "text": "—"})
    return findings


# --------------------------------------------------------------------------- research ledger
TAGS = ("observed", "inferred", "unknown")
URL_OR_FILE = re.compile(r"https?://\S+|(\.oeo/|\./|/)\S+\.(md|png|jpg|html|txt|json|har)\b", re.I)
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def ledger_check(text):
    """Rules from oeo:research: tag in observed/inferred/unknown; observed needs a URL or file plus an
    access date; inferred names what it is inferred from; unknown states its search boundary."""
    problems, rows_seen = [], 0
    for header, rows in md_tables(text):
        t_col = column(header, "observed", "tag", "type")
        e_col, b_col, c_col = column(header, "evidence", "source"), column(header, "boundary"), column(header, "claim")
        if t_col is None or e_col is None:
            continue
        for i, r in enumerate(rows, 1):
            rows_seen += 1
            cell = lambda c: r[c] if c is not None and c < len(r) else ""  # noqa: E731
            tag, ev, claim = cell(t_col).lower().strip("* `"), cell(e_col), cell(c_col)[:50]
            where = f"row {i} ({claim})"
            if tag not in TAGS:
                problems.append(f"{where}: tag '{tag}' must be observed, inferred or unknown")
            elif tag == "observed" and not (URL_OR_FILE.search(ev) and DATE.search(ev)):
                problems.append(f"{where}: observed claims need a URL or file and an access date")
            elif tag == "inferred" and not ev.strip():
                problems.append(f"{where}: inferred claims must say what they are inferred from")
            elif tag == "unknown" and not cell(b_col).strip():
                problems.append(f"{where}: unknown claims must state the search boundary")
    if not rows_seen:
        problems.append("no ledger table found (need columns: claim | observed/inferred/unknown | evidence | boundary)")
    return problems


# --------------------------------------------------------------------------- verification / brief / release
def verification_check(text, required_gates=()):
    """Every gate row has a result (PASS, FAIL, N/A: reason) and PASS rows carry evidence; all
    required gates are present; nothing reads FAIL or NOT RUN."""
    problems, seen = [], {}
    for header, rows in md_tables(text):
        g, r, e = column(header, "gate"), column(header, "result", "verdict"), column(header, "evidence")
        if g is None or r is None:
            continue
        for row in rows:
            cell = lambda c: row[c].strip() if c is not None and c < len(row) else ""  # noqa: E731
            gate, result, ev = cell(g).strip("` "), cell(r), cell(e)
            if not gate:
                continue
            seen[gate] = result
            up = result.upper()
            if up.startswith("PASS") and e is not None and not ev:
                problems.append(f"{gate}: PASS without evidence")
            elif up.startswith("N/A") and not re.search(r"N/A\s*:?\s*\S{3,}", result, re.I):
                problems.append(f"{gate}: N/A needs a reason")
            elif "FAIL" in up or "NOT RUN" in up:
                problems.append(f"{gate}: {result}")
            elif not (up.startswith("PASS") or up.startswith("N/A")):
                problems.append(f"{gate}: result must be PASS, FAIL or N/A: <reason>, got '{result}'")
    if not seen:
        problems.append("no gate table found (| gate | method | result | evidence |)")
    problems += [f"{g}: required gate missing" for g in required_gates if g not in seen]
    return problems


BRIEF_SECTIONS = ("users", "outcome", "metric", "non-goal", "acceptance criteria")


def brief_check(text):
    """Brief rules from oeo:business-review: required sections, no TBD, evidence labels, testable criteria."""
    low, problems = text.lower(), []
    problems += [f"missing section: {s}" for s in BRIEF_SECTIONS if s not in low]
    if re.search(r"\bTBD\b", text):
        problems.append("contains TBD: move unknowns to assumptions / open questions")
    if not re.search(r"\b(FACT|HYPOTHESIS|UNKNOWN|OPINION)\b", text):
        problems.append("no evidence labels (FACT / HYPOTHESIS / UNKNOWN / OPINION)")
    crit = re.split(r"acceptance criteria", text, flags=re.I)[-1] if "acceptance criteria" in low else ""
    if len(re.findall(r"^\s*(\d+[.)]|[-*])\s+\S", crit, re.M)) < 1:
        problems.append("no numbered or bulleted acceptance criteria")
    return problems


SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[\w.]+)?$")


def release_check(changelog, version, version_sources=()):
    """Keep a Changelog + SemVer: a dated section for `version`, an Unreleased section kept, every
    version source equal to `version`. `version_sources` is a list of (name, text)."""
    problems = []
    if not SEMVER.match(version or ""):
        problems.append(f"'{version}' is not a SemVer version")
    m = re.search(r"^## \[" + re.escape(version) + r"\] - (\d{4}-\d{2}-\d{2})\s*$", changelog, re.M)
    if not m:
        problems.append(f"CHANGELOG has no '## [{version}] - YYYY-MM-DD' section")
    else:
        body = re.split(r"^## \[", changelog[m.end():], maxsplit=1, flags=re.M)[0]
        if not re.search(r"^### (Added|Changed|Deprecated|Removed|Fixed|Security)", body, re.M):
            problems.append(f"the {version} section has no Keep a Changelog subsection")
    if not re.search(r"^## \[Unreleased\]", changelog, re.M):
        problems.append("CHANGELOG lost its '## [Unreleased]' section")
    for name, text in version_sources:
        if version not in text:
            problems.append(f"{name} does not contain version {version}")
    return problems
