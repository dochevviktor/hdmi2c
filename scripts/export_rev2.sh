#!/usr/bin/env bash
# Regenerate the checked CAD review/prototype package. Never orders a PCB.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd -- "$project_dir"
artifact_dir="$project_dir/hardware/rev2"
mkdir -p "$artifact_dir/checks" "$artifact_dir/fabrication"

# Fail before producing manufacturing outputs if electrical/CAD checks fail.
bash scripts/validate_rev2.sh "$artifact_dir"

kicad-cli sch export pdf --output "$artifact_dir/schematic.pdf" hdmi2c.kicad_sch
kicad-cli sch export bom --fields 'Reference,Value,Footprint,QUANTITY,Manufacturer,MPN,LCSC Part #,Specification,Datasheet' \
  --labels 'References,Value,Footprint,Quantity,Manufacturer,MPN,LCSC Part #,Specification,Datasheet' \
  --group-by Value,Footprint,MPN,Specification --output "$artifact_dir/bom-design.csv" hdmi2c.kicad_sch
kicad-cli pcb export pos --side front --format csv --units mm \
  --output "$artifact_dir/positions-front.csv" hdmi2c.kicad_pcb
# Separate upload schema from the raw KiCad export and the purchasing BOM.
# This maps columns/units only; custom-part offsets and all rotations need review.
python3 scripts/export_jlcpcb_cpl.py "$artifact_dir/positions-front.csv" \
  "$artifact_dir/bom-jlcpcb-draft.csv" --output "$artifact_dir/cpl-jlcpcb-draft.csv" \
  --report "$artifact_dir/checks/jlcpcb-cpl.json"

# Fabrication drawings retain a full sheet so connector overhang is visible.
kicad-cli pcb export svg --layers F.Fab,F.SilkS,Edge.Cuts --sketch-pads-on-fab-layers \
  --black-and-white --scale 4 --mode-single --output "$artifact_dir/assembly-front.svg" hdmi2c.kicad_pcb
kicad-cli pcb export svg --layers B.Fab,B.SilkS,Edge.Cuts --sketch-pads-on-fab-layers \
  --black-and-white --scale 4 --mirror --mode-single --output "$artifact_dir/assembly-back.svg" hdmi2c.kicad_pcb
kicad-cli pcb export pdf --layers F.Fab,Edge.Cuts --sketch-pads-on-fab-layers \
  --black-and-white --scale 1 --mode-single --output "$artifact_dir/fit-check-1to1.pdf" hdmi2c.kicad_pcb
kicad-cli pcb export svg --layers F.Cu,F.SilkS,Edge.Cuts --fit-page-to-board \
  --mode-single --output "$artifact_dir/copper-front.svg" hdmi2c.kicad_pcb
kicad-cli pcb export svg --layers B.Cu,B.SilkS,Edge.Cuts --fit-page-to-board \
  --mirror --mode-single --output "$artifact_dir/copper-back.svg" hdmi2c.kicad_pcb

# Nominal assembly geometry, not a physical fit or RF qualification.
# Requires KiCad's standard 3D-model library in addition to the local models.
kicad-cli pcb export step --force --output "$artifact_dir/assembly.step" hdmi2c.kicad_pcb
kicad-cli pcb render --width 1400 --height 900 --quality high --rotate '330,0,30' \
  --output "$artifact_dir/assembly-3d-front.png" hdmi2c.kicad_pcb
kicad-cli pcb render --width 1400 --height 900 --quality high --side bottom --rotate '30,0,30' \
  --output "$artifact_dir/assembly-3d-back.png" hdmi2c.kicad_pcb

# Gerbers, drills and positions all use the absolute KiCad origin, in mm.
kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Paste,B.Paste,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts \
  --output "$artifact_dir/fabrication/" hdmi2c.kicad_pcb
kicad-cli pcb export drill --format excellon --drill-origin absolute --excellon-units mm \
  --excellon-oval-format route --excellon-separate-th --generate-map --map-format pdf \
  --output "$artifact_dir/fabrication/" hdmi2c.kicad_pcb

# Hash the exact source inputs to make stale output packages recognizable.
sha256sum hdmi2c.kicad_sch hdmi2c.kicad_pcb hdmi2c.kicad_pro hdmi2c.kicad_sym \
  hdmi2c.pretty/XIAO_ESP32C6_Castellated.kicad_mod \
  hdmi2c.pretty/WURTH_685119134923_HDMI.kicad_mod \
  3d/Seeed_Studio_XIAO_ESP32C6.step 3d/WURTH_685119134923_HDMI.STEP \
  hardware/rev2/bom.csv \
  > "$artifact_dir/checks/source-sha256.txt"
echo 'Solid-clearance review is separate: see hardware/rev2/README.md to refresh its hashed report.'
echo "Prototype package updated: $artifact_dir (physical validation still required)."
