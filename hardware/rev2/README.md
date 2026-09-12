# Rev2 prototype package

**CAD-checked; not built or electrically tested. Do not treat this as a qualified
production release.** Read the [hardware notes](../../docs/stage2-hardware.md)
before fabrication or assembly. No order or external publication was performed.

- [Schematic PDF](schematic.pdf)
- [BOM](bom.csv): 12 fitted components, including the purchased XIAO module.
  Generic passives must meet the stated voltage, dielectric, power, and tolerance
  specifications. Source availability and assembler substitutions need review.
- [Front assembly](assembly-front.svg) and [back assembly](assembly-back.svg):
  enlarged 4:1 drawings; the back view is mirrored. All fitted parts are front-side;
  the four back test pads are not fitted components.
- [1:1 fit-check PDF](fit-check-1to1.pdf): print at 100%, with page fitting disabled.
  Confirm the carrier measures 42 × 24 mm before comparing actual parts.
- [Front copper](copper-front.svg) and [back copper](copper-back.svg).
- [Placement data](positions-front.csv): mm, absolute KiCad origin, standard
  KiCad rotations. **U3's footprint origin is not its body centroid**; the assembler
  must check its machine origin and rotation. J7 is mixed SMT/plated-slot assembly
  and is included in this file, not omitted as a non-SMD part.
- [Fabrication files](fabrication/): two copper layers, both solder masks and
  silkscreens, paste, outline, plated/non-plated Excellon drills, and drill maps.
  There are 33 plated 0.3 mm vias and four plated 0.9 mm-wide routed HDMI shell
  slots. The separate NPTH drill file and back-paste layer are intentionally empty.
- [ERC report](checks/erc.json), [DRC/parity report](checks/drc.json),
  [netlist](checks/netlist.xml), and [source hashes](checks/source-sha256.txt).

Fabrication assumptions: 2 layers, 1.6 mm FR-4, nominal 35 µm (1 oz) copper;
0.20 mm minimum tracks/clearance, 0.60/0.30 mm vias, 0.30 mm copper-to-edge
clearance. Confirm these, mask web capability, routed plated slots, and stencil
handling of the XIAO with the fabricator. The 42 × 24 mm measurement excludes
connector overhangs. There are no mounting holes; provide enclosure support.

Regenerate from the project root with KiCad 10 and its standard symbol/footprint
libraries plus the `pcbnew` Python module:

```sh
bash scripts/export_rev2.sh
sha256sum -c hardware/rev2/checks/source-sha256.txt
```

The export script runs ERC, DRC/parity, the electrical/mechanical contract check,
and six fault-injection tests before exporting production-format files. If it
fails, do not use earlier output files as a release for the newly edited design.
The existing upstream Pages workflow was not upgraded or tested; these checked-in
files and the local script are the rev2 handoff.
