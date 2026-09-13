#!/usr/bin/env bash
# Shared local/CI CAD checks. A pass is not approval to order or assemble.
set -euo pipefail
if [[ $# != 1 ]]; then
  echo 'Usage: bash scripts/validate_rev2.sh OUTPUT_DIRECTORY' >&2
  exit 2
fi
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$project_dir"
case "$(kicad-cli version)" in
  10.*) ;;
  *) echo 'Rev2 validation requires KiCad 10 and its standard libraries.' >&2; exit 2 ;;
esac
artifact_dir="$(realpath -m -- "$1")"
mkdir -p "$artifact_dir/checks"

kicad-cli sch erc --exit-code-violations --format json \
  --output "$artifact_dir/checks/erc.json" hdmi2c.kicad_sch
kicad-cli pcb drc --schematic-parity --all-track-errors --exit-code-violations \
  --format json --output "$artifact_dir/checks/drc.json" hdmi2c.kicad_pcb
kicad-cli sch export netlist --format kicadxml \
  --output "$artifact_dir/checks/netlist.xml" hdmi2c.kicad_sch
python3 scripts/check_rev2.py hdmi2c.kicad_pcb "$artifact_dir/checks/netlist.xml"
python3 -m unittest discover -s tests -v

# The matching CSV is read-only input. Every identity/footprint mismatch fails;
# a matching BOM is still not approval of placement or the assembly process.
python3 scripts/check_jlcpcb_bom.py hardware/rev2/bom.csv "$artifact_dir/checks/netlist.xml" \
  --report "$artifact_dir/checks/jlcpcb-bom.json" \
  --draft-bom "$artifact_dir/bom-jlcpcb-draft.csv"
