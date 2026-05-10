#!/bin/bash
# ~/.local/bin/get-last-msg

# Find the current project's transcript dir
PROJECT_KEY=$(pwd | sed 's|^/||' | sed 's|/|-|g')
TRANSCRIPT_DIR="$HOME/.claude/projects/$PROJECT_KEY"

# Alternatively check new config dir location (Claude Code v1.0.30+)
if [ ! -d "$TRANSCRIPT_DIR" ]; then
  TRANSCRIPT_DIR="$HOME/.config/claude/projects/$PROJECT_KEY"
fi

# Get most recently modified transcript
TRANSCRIPT=$(ls -t "$TRANSCRIPT_DIR"/*.jsonl 2>/dev/null | head -1)

if [ -z "$TRANSCRIPT" ]; then
  echo "No transcript found for $(pwd)" >&2
  exit 1
fi

# Extract last assistant text message
jq -r 'select(.type=="assistant") | .message.content[] | select(.type=="text") | .text' \
  "$TRANSCRIPT" | tail -1