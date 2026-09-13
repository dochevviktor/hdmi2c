#!/usr/bin/env bash
# Build a 2D review preview, never an assembly/fabrication release.
set -euo pipefail
if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo 'Usage: bash scripts/build_review_site.sh INTERACTIVE_HTML_BOM_DIRECTORY [NEW_OUTPUT_DIRECTORY]' >&2
  exit 2
fi
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$project_dir"
ibom_dir="$(realpath -m -- "$1")"
site_dir="$(realpath -m -- "${2:-out}")"
if [[ ! -f "$ibom_dir/InteractiveHtmlBom/generate_interactive_bom.py" || ! -f "$ibom_dir/LICENSE" ]]; then
  echo 'Expected an InteractiveHtmlBom checkout (CI pins v2.12.0).' >&2
  exit 2
fi
# Never merge stale assets into the preview, or delete an existing directory.
# In particular, do not accidentally publish STEP/renders or the raw matching CSV.
if [[ -e "$site_dir" || -L "$site_dir" ]]; then
  echo 'Preview output must be a new directory; choose another output path.' >&2
  exit 2
fi
mkdir -p "$site_dir"
bash scripts/validate_rev2.sh "$site_dir"

kicad-cli sch export pdf --output "$site_dir/schematic.pdf" hdmi2c.kicad_sch
kicad-cli sch export bom --fields 'Reference,Value,Footprint,QUANTITY,Manufacturer,MPN,LCSC Part #,Specification,Datasheet' \
  --labels 'References,Value,Footprint,Quantity,Manufacturer,MPN,LCSC Part #,Specification,Datasheet' \
  --group-by Value,Footprint,MPN,Specification --output "$site_dir/bom-design.csv" hdmi2c.kicad_sch
INTERACTIVE_HTML_BOM_NO_DISPLAY=1 python3 "$ibom_dir/InteractiveHtmlBom/generate_interactive_bom.py" \
  --no-browser --dest-dir "$site_dir" --name-format hdmi2c-iBOM \
  --blacklist TP1,TP2,TP3,TP4 --extra-data-file hdmi2c.kicad_pcb \
  --extra-fields 'MPN,LCSC Part #' hdmi2c.kicad_pcb
cp docs/review-site.html "$site_dir/index.html"
cp "$ibom_dir/LICENSE" "$site_dir/InteractiveHtmlBom-LICENSE.txt"

# Record inputs, including tool versions, without publishing the model files.
sha256sum hdmi2c.kicad_sch hdmi2c.kicad_pcb hdmi2c.kicad_pro hdmi2c.kicad_sym \
  hdmi2c.pretty/XIAO_ESP32C6_Castellated.kicad_mod \
  hdmi2c.pretty/WURTH_685119134923_HDMI.kicad_mod \
  3d/Seeed_Studio_XIAO_ESP32C6.step 3d/WURTH_685119134923_HDMI.STEP \
  hardware/rev2/bom.csv > "$site_dir/checks/source-sha256.txt"
kicad-cli version > "$site_dir/checks/kicad-version.txt"
INTERACTIVE_HTML_BOM_NO_DISPLAY=1 python3 "$ibom_dir/InteractiveHtmlBom/generate_interactive_bom.py" --version \
  > "$site_dir/checks/ibom-version.txt"
git -c safe.directory="$project_dir" rev-parse HEAD > "$site_dir/checks/commit.txt"
echo "Review preview built: $site_dir (JLCPCB assembly remains blocked)."
