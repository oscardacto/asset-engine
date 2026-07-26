#!/bin/bash
# Hook: PreToolUse (Bash|PowerShell) — wrapper de command-write-protection.js
exec node "$(dirname "$0")/command-write-protection.js"
