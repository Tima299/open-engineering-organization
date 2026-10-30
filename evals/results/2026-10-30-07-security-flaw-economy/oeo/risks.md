| risk | likelihood | impact | mitigation | owner |
|---|---|---|---|---|
| Owner is caller-supplied; HTTP layer must bind identity (BA F2) | high at exposure | blocker | identity contract before HTTP work | technical-architect |
| open_task_counts() leaks all owners (BA F3) | medium | major | restrict or scope by owner | security-engineer |
| No input validation (BA F4) | medium | major at HTTP | separate Class B ticket | project-manager |
| complete() unknown id -> TypeError (BA F5, seeded defect) | high | minor | separate Class B ticket | project-manager |
| sqlite cross-thread use (BA F7) | unknown | major if threaded | decide server model | technical-architect |
