#!/bin/bash
# Hook: PreToolUse (Edit|Write) — wrapper de pre-edit-protection.js (ver ese archivo para la lógica)
exec node "$(dirname "$0")/pre-edit-protection.js"
