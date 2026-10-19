#!/bin/sh
# Build the project guide and the presentation transcript (needs Google Chrome).
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for n in guide transcript; do
  [ -f "src/$n.html" ] || continue
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer --allow-file-access-from-files \
    --print-to-pdf="$n.pdf" "file://$PWD/src/$n.html" 2>/dev/null
  echo "wrote docs/guide/$n.pdf"
done
