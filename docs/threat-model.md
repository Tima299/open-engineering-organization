# Threat model

Scope: the OEO plugin (skills, agents, hooks, `scripts/`) running inside Claude Code on a
developer machine or CI, operating on a target repository. Method: STRIDE-style per asset,
reviewed on every change to hooks, scripts, agent tool lists or routing. Verification checklist:
[skills/verify/references/security.md](../skills/verify/references/security.md).

## Assets and trust boundaries
| Asset | Boundary |
|---|---|
| Target repository code and history | Agents may edit; destructive git operations need approval |
| Secrets on the machine (env files, keys, tokens) | Must never enter transcripts, handoffs or commits |
| User authorization (what may be published, deployed, spent) | Only the human grants it |
| OEO policy files (`org/`, `config/`) | Trusted only as shipped in the installed plugin version |
| Repository, issue, web and tool-output content | **Untrusted data**, never instructions |

## Threats and mitigations
| # | Threat | Mitigation | Residual risk |
|---|---|---|---|
| T1 | Prompt injection in repo files/issues/web pages redirects an agent | Agent preamble declares all such content data; precedence policy level rule; reviewers report injection attempts; eval scenario `15-prompt-injection` | Model compliance is probabilistic; human review of consequential actions remains the backstop |
| T2 | Destructive shell command (rm -rf, reset --hard, DROP, terraform destroy) | `scripts/guard.py` PreToolUse turns them into a confirmation prompt; Claude Code permissions | Pattern guard is bypassable (aliases, scripts, encodings); it is defense in depth, not a sandbox. If `python3` cannot start, Claude Code proceeds without the guard (hooks fail open) |
| T3 | Unauthorized publication (force push, publish, release, tag push) | Guard asks; release skill requires explicit approval | Same as T2 |
| T4 | Secret written into a file or printed into the transcript | Guard detects common token formats on Write/Edit and secret-file reads | Unknown token formats and secrets via Bash redirects are not caught |
| T5 | Privilege creep through agent tools | Contracts use least-privilege capabilities; reviewers (QA, security, BA) get no edit tools; generated `tools:` lists are checked in CI | Generic agents share one tool set across contracts |
| T6 | Supply chain: malicious/typosquatted dependency or third-party skill | License gate + provenance registry; OEO vendors no third-party skills and has zero runtime dependencies; dev dependency pinned with hash; Actions pinned by SHA | Adapters the user installs run with their own hooks (documented per entry) |
| T7 | Authz regression or cross-tenant leak in the target product | Risky domains force Class C, which activates the security engineer and deny-path tests | Depends on test quality in the target repo |
| T8 | Unsafe migration / data loss | `database` domain activates the database engineer; checklist requires rollback or forward-fix | Production data shape unknown to the agent |
| T9 | Tampered OEO policy in a fork or PR | CODEOWNERS on `org/`, `config/`, `scripts/`, `hooks/`; CI validation; signed release tags | Users installing from unofficial forks |
| T10 | Cost exhaustion (runaway agents) | Class budgets, retry budget, FinOps report, Class A/B use cheaper tiers | Main-session tokens are not measured by the hook |
| T11 | Local logs leak information | `.oeo/` logs stay local, contain summaries and token counts only, never prompts or secrets; nothing is sent anywhere | A user may commit logs; docs recommend ignoring `*.jsonl` |
| T12 | Instructions hidden in fetched web pages or community posts steer research or design work | `oeo:research` runs in an isolated subagent, saves pages to files, treats them as data, and tags claims observed/inferred/unknown with sources (no eval for web-page injection yet) | A persuasive page can still bias conclusions; humans review the finding ledger |
| T13 | Legal exposure from reverse engineering or scraping a company's product | Authorization gate first: public evidence by default; reverse engineering only with the user's authorization; no DRM/auth bypass, no login scraping, no copying code or assets | The user's authorization claim is not verified by OEO |
| T14 | Spend on paid external tools (Firecrawl, scraping APIs) | `oeo:finops` credit rules: honor caps, stop when usage is unknown, auth/credit errors are terminal; adapters are never installed automatically | Paid usage is not measured by OEO's hook; it relies on the tool's own reporting |

## Out of scope
Security of Claude Code itself, of model providers, and of third-party adapters (report to
their maintainers). OEO's scripts and hooks add no network calls and no telemetry; web access
happens only through Claude Code's tools when the user asks for research (T12-T14).
