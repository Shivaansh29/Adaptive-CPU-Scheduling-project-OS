#!/bin/sh
# Rebuild the PDFs in docs/ from the HTML sources in docs/src/ (needs Google Chrome).
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for name in project_review ieee_paper; do
  [ -f "src/$name.html" ] || continue
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer --allow-file-access-from-files \
    --print-to-pdf="$name.pdf" "file://$PWD/src/$name.html" 2>/dev/null
  echo "wrote docs/$name.pdf"
done
