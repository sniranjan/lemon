#!/bin/bash
# Post the next N reels from marketing/instagram/reels/queue.txt (default 3), each also shared to the story,
# with a gap between them (default 20 minutes). Already-posted reels are skipped (posted.jsonl).
#   scripts/marketing/reel_daily.sh [N] [GAP_MINUTES] [--dry-run]   (--dry-run: list what would post, post nothing)
cd "$(dirname "$0")/../.."
n=${1:-3}; gap=${2:-20}; done_count=0
today=$(date +%F); dry=0; [[ " $* " == *" --dry-run "* ]] && dry=1
while read -r dir; do
  [[ -z "$dir" || "$dir" == \#* ]] && continue
  if [[ "$dir" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})\ +(.+)$ ]]; then  # "2026-12-01 path": not before that date
    [[ "${BASH_REMATCH[1]}" > "$today" ]] && continue
    dir=${BASH_REMATCH[2]}
  fi
  grep -q "\"post:$dir\"" marketing/instagram/posted.jsonl && continue
  if [ $dry = 1 ]; then echo "would post: $dir"; done_count=$((done_count + 1)); [ $done_count -ge $n ] && break; continue; fi
  [ $done_count -gt 0 ] && sleep $((gap * 60))
  uv run python scripts/marketing/ig_publish.py "$dir" | tail -1 || exit 1
  uv run python scripts/marketing/ig_publish.py "$dir" --story | tail -1
  done_count=$((done_count + 1)); [ $done_count -ge $n ] && break
done < marketing/instagram/reels/queue.txt
echo "posted $done_count reel(s)"
