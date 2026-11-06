#!/usr/bin/env bash
# SessionStart hook for the plugin install.
# Prints the always-on rules from CLAUDE.md, with every
# .claude/skills/bash-slim/... path pointing at this plugin's copy (quoted, forward slashes).
root=${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}
root=$(printf '%s' "$root" | sed 's#\\#/#g')
sed "s#\.claude/skills/bash-slim/\([A-Za-z0-9._/-]*\)#\"$root/.claude/skills/bash-slim/\1\"#g" "$root/CLAUDE.md"
