#!/bin/bash
# Render every level reel and topic reel to out/<id>.mp4.
cd "$(dirname "$0")"
ids=$(npx remotion compositions 2>/dev/null | grep -oE '(Level|Topic)-[a-z0-9-]+' | sort -u)
for id in $ids; do npx remotion render "$id" "out/$id.mp4" --log=error || echo "FAILED $id"; done
echo done
