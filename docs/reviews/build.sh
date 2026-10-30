#!/bin/sh
# Build the review PDFs from src/*.html (needs Google Chrome).
#   sh docs/reviews/build.sh        # Review_1, Review_2 and Review_3
#   sh docs/reviews/build.sh 3      # only Review_3 (Reviews 1 and 2 are final)
# Review 3's HTML is generated first:  python3 docs/reviews/src/number_refs.py
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for n in ${@:-1 2 3}; do
  [ -f "src/review$n.html" ] || continue
  "$CHROME" --headless --disable-gpu --no-pdf-header-footer --allow-file-access-from-files \
    --print-to-pdf="Review_$n.pdf" "file://$PWD/src/review$n.html" 2>/dev/null
  echo "wrote docs/reviews/Review_$n.pdf"
done
