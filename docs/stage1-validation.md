# Single-HDMI hardware revision

Revision: `rev1`, 2026-09-12. Stage 1 is complete in CAD. This is an intermediate
ESP32-WROOM-32 design; the XIAO carrier and ESPHome firmware are still planned.
The board has not been built or tested on a monitor, and the inherited findings
below must be reviewed before fabrication.

## Changes

- Kept HDMI1 (`J7`) and its complete DDC level shifting, HPD divider, shield jumper,
  switchable 5 V supply, and I2C jumpers.
- Removed `J8`, `JP2`, `JP7`, `JP8`, `Q4`, `Q6`, `Q8`, `R8`, `R10`, `R12`,
  `R14`, `R20`, `R21`, `U5`, and `C6` from schematic and PCB, together with their
  nets and routing. Removed dedicated branches of the shared power/ground nets.
- Marked U3 pins 8, 9, 28, and 31 (GPIO32, GPIO33, GPIO17, GPIO19) as intentionally
  unconnected. Their old HDMI2/I2C2 signal labels and traces are gone.
- Reduced the outline from 95 × 45 mm to 70 × 45 mm: 4,275 to 3,150 mm², a 26.3%
  area reduction. Moved the two right mounting holes 25 mm left while preserving
  the corner radius and hole-to-edge spacing.
- Moved the copper logo above the MCU, scaled it to 80%, and updated its revision
  glyph to `rev1`. Updated the local footprint library to match. The original
  creator's name and 2021 artwork attribution remain.
- Refilled the bottom ground plane. Kept the original schematic format 20211123
  and PCB format 20211014, without a wholesale KiCad format conversion.
- Reduced the populated circuit from 56 to 41 component footprints. Total PCB
  footprints went from 61 to 46, including four mounting holes and one logo.

## Retained pin mapping

This table is for the stage-1 WROOM design. Stage 2 will define the XIAO mapping.

| Function | ESP32-WROOM-32 | HDMI connector / path |
| --- | --- | --- |
| DDC SCL | GPIO26, U3 pin 11 | JP3 → Q3 → J7 pin 15 |
| DDC SDA | GPIO27, U3 pin 12 | JP4 → Q5 → J7 pin 16 |
| HPD sense | GPIO16, U3 pin 27 | J7 pin 19 → R18/R19 divider |
| HDMI 5 V enable | GPIO18, U3 pin 30 | U4 enable → Q7 → J7 pin 18 |
| DDC ground | GND | J7 pin 17 |

## Verification results

Compared against the original schematic/PCB at commit
`3f064aa6c761e88b313b9f9e71b1f0dff42e0744`, using the user's existing project
settings and KiCad CLI 10.0.6. The existing `hdmi2c.kicad_pro` changes were preserved
byte-for-byte. Both baseline and revised DRC runs refilled zones.

| Check | Original | Stage 1 |
| --- | ---: | ---: |
| HDMI connectors | 2 | 1 |
| Unrouted connections (DRC) | 0 | 0 |
| ERC errors | 12 | 7 |
| ERC warnings | 351 | 257 |
| DRC errors | 18 | 10 |
| DRC warnings | 58 | 41 |
| Schematic/PCB parity warnings | 115 | 90 |
| New ERC/DRC/parity findings, compared by rule and item UUIDs | — | 0 |

Independent connectivity comparison passed for all **88 remaining pin groups**:

1. The PCB's assigned pin groups match the exported schematic netlist.
2. The revised schematic equals the original schematic after removing the 15
   deleted components. Every retained pin connection, including the complete
   HDMI1 and shared supply circuits, is preserved.

This comparison deliberately ignores automatic net-name spelling, which differs
between KiCad generations. Physical routing was checked separately by DRC.
Schematic PDF/SVG and PCB copper/outline views exported successfully and were
visually inspected. `git diff --check` passed.

## Inherited findings to resolve before a release

- Seven ERC power-drive errors: J7's four TMDS shield pins, HDMI1 5 V, and the
  GND/VBUS supply declarations. The shield nets are currently isolated labels;
  review the electrical intent and power flags during the XIAO redesign.
- Eight DRC errors concern copper bridges in the retained JP3/JP4 solder-jumper
  footprints: four solder-mask bridge, two clearance, and two shorting findings.
  These are the original bridged-jumper geometry and net representation; review
  the footprint/net-tie modeling rather than suppressing the entire rule.
- Two DRC errors are the existing C3 courtyard overlaps with J1 and U1 in the
  USB/serial section. This section is due to be replaced by the XIAO.
- Remaining ERC warnings: 216 off-grid endpoints, 33 symbol-library mismatches,
  five isolated labels, and three symbol-library issues.
- Remaining DRC warnings: 39 footprint-library mismatches and two silkscreen
  edge-clearance findings.
- Parity warnings: 76 legacy net-name differences, nine datasheet-field
  differences, and five PCB-only footprints (mounting holes and artwork).

These counts are recorded findings, not a claim of a clean manufacturing check.
No rule severities or exclusions were changed to obtain the results. Stage 2
must review the power circuit and resolve remaining release-blocking findings;
physical power, DDC, and monitor compatibility tests are still outstanding.

## Repeating the checks

From the repository root, with KiCad CLI and its `pcbnew` Python module installed:

```sh
task_checks="$(mktemp -d)"
kicad-cli sch export netlist --format kicadxml \
  -o "$task_checks/netlist.xml" hdmi2c.kicad_sch
python3 scripts/check_connectivity.py hdmi2c.kicad_pcb "$task_checks/netlist.xml"
kicad-cli sch erc --format json \
  -o "$task_checks/erc.json" hdmi2c.kicad_sch
kicad-cli pcb drc --refill-zones --schematic-parity --format json \
  -o "$task_checks/drc.json" hdmi2c.kicad_pcb
git diff --check
```

Inspect the JSON reports: the CLI normally exits successfully even when it finds
violations. Add `--exit-code-violations` for a strict gate, which currently fails
on the inherited findings. Avoid `--save-board` on the working file unless a
KiCad format migration is intended.

The connectivity helper also accepts `--baseline-netlist <original.xml>` and
`--removed J8 JP2 JP7 JP8 Q4 Q6 Q8 R8 R10 R12 R14 R20 R21 U5 C6` to repeat the
stage-1 preservation check using an exported original netlist. It does not replace
ERC, DRC, or physical measurements.
