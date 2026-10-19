#!/bin/sh
# Build the three review PDFs from src/*.html (needs Google Chrome).
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for n in 1 2 3; do
  [ -f "src/review$n.html" ] || continue
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer --allow-file-access-from-files \
    --print-to-pdf="Review_$n.pdf" "file://$PWD/src/review$n.html" 2>/dev/null
  echo "wrote docs/reviews/Review_$n.pdf"
done
