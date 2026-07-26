#!/bin/bash
# Hook: PreToolUse — wrapper de rules-inject.js (ver ese archivo para la lógica real)
exec node "$(dirname "$0")/rules-inject.js"
