#!/bin/bash
# Render every level, topic and facts reel to out/<id>.mp4.
cd "$(dirname "$0")"
ids=$(npx remotion compositions 2>/dev/null | grep -oE '(Level|Topic|Facts)-[a-z0-9-]+' | sort -u)
for id in $ids; do npx remotion render "$id" "out/$id.mp4" --log=error || echo "FAILED $id"; done
echo done
