# 0001. Ship as a Claude Code plugin with a self-hosted marketplace

- Status: Accepted
- Date: 2026-10-30

## Context
Users need a one-command install and a clean uninstall. Official Claude Code docs (accessed
2026-10-30) define plugins (`.claude-plugin/plugin.json`, `skills/`, `agents/`, `hooks/hooks.json`)
and marketplaces (`.claude-plugin/marketplace.json`, plugin `source: "./"`). Uninstall removes the
plugin and its data directory.

## Options
1. **Plugin + own marketplace in this repo**: official format, namespaced skills (`/oeo:deliver`), versioned, removable.
2. Copy files into `~/.claude/`: no versioning, no clean uninstall, collisions with user files.
3. A standalone agent framework: portable, but reimplements what the host already does well.

## Decision
Option 1. The repository root is both the marketplace and the single plugin `oeo`.

## Consequences
Install = `/plugin marketplace add Tima299/open-engineering-organization` + `/plugin install
oeo@open-engineering-organization`. We depend on the plugin format staying stable; contracts and
policy stay host-neutral (ADR 0002, 0003) so another host adapter remains possible.

## Revisit when
The plugin format changes incompatibly, or users need a non-Claude-Code host.
