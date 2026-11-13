#!/bin/bash
# Hourly on the ROG (systemd user timer themes-refresh.timer): fetch the newest titles, give new ones a theme, publish.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
git pull -q --rebase --autostash
out=$(.venv/bin/python refresh_themes.py)
echo "$out"
[[ $out == changed* ]] || exit 0
git commit -q -m "Themes refresh: $(echo "$out" | head -1 | cut -d' ' -f2-)" -- themes.json labels.json
git push -q || { git pull -q --rebase --autostash && git push -q; }
