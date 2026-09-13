# Rev2 prototype package

**CAD-checked; not built or electrically tested. Do not treat this as a qualified
production release.** Read the [hardware notes](../../docs/stage2-hardware.md)
before fabrication or assembly. No order or external publication was performed.
JLCPCB preparation is documented in [JLCPCB notes](../../docs/jlcpcb.md).
**J7 is now matched to C2930961; final placement and assembler approval remain pending.**

- [Schematic PDF](schematic.pdf)
- [Engineering BOM](bom-design.csv): 12 fitted components, including the XIAO,
  with reviewed specifications and purchasing fields.
- [JLCPCB matching CSV](bom.csv): user-managed snapshot with J7 explicitly
  corrected to C2930961. Other rows are preserved; this is not the clean upload BOM.
- [JLCPCB draft BOM](bom-jlcpcb-draft.csv) and [BOM audit](checks/jlcpcb-bom.json):
  seven matched part groups / 12 components; J7 is the existing Würth socket,
  685119134923 / C2930961. Still a draft pending assembly review, not a release.
- [Front assembly](assembly-front.svg) and [back assembly](assembly-back.svg):
  enlarged 4:1 drawings; the back view is mirrored. All fitted parts are front-side;
  the four back test pads are not fitted components.
- [1:1 fit-check PDF](fit-check-1to1.pdf): print at 100%, with page fitting disabled.
  Confirm the carrier measures 42 × 24 mm before comparing actual parts.
- [Front copper](copper-front.svg) and [back copper](copper-back.svg).
- [3D front view](assembly-3d-front.png), [3D back view](assembly-3d-back.png), and
  [assembly STEP](assembly.step): include the detailed XIAO and all 12 fitted parts.
  Nominal envelope is about 43.90 × 25.51 × 8.38 mm, excluding cables and solder.
  The supplied XIAO model is from 2024; check the actual module revision and the
  [model provenance/redistribution caveat](../../3d/README.md) before reuse.
- [Placement data](positions-front.csv): mm, absolute KiCad origin, standard
  KiCad rotations. **U3's footprint origin is not its body centroid**; the assembler
  must check its machine origin and rotation. This is not a finalized JLCPCB CPL;
  U3 and J7 require offset/rotation review. J7 is mixed SMT/plated-slot assembly
  and is included in this file, not omitted as a non-SMD part.
- [JLCPCB draft CPL](cpl-jlcpcb-draft.csv) and [CPL report](checks/jlcpcb-cpl.json):
  those 12 placements in JLCPCB's `Designator,Mid X,Mid Y,Layer,Rotation` format.
  XY and rotations are unchanged, so U3/J7 still need centroid corrections and all
  rotations need placement-preview review.
- [Fabrication files](fabrication/): two copper layers, both solder masks and
  silkscreens, paste, outline, plated/non-plated Excellon drills, and drill maps.
  There are 33 plated 0.3 mm vias and four plated 0.9 mm-wide routed HDMI shell
  slots. The separate NPTH drill file and back-paste layer are intentionally empty.
- [ERC report](checks/erc.json), [DRC/parity report](checks/drc.json),
  [netlist](checks/netlist.xml), [source hashes](checks/source-sha256.txt), and
  [nominal 3D clearance report](checks/mechanical-3d.json). The latter records
  source and STEP hashes; it is not evidence of a physical fit or RF test.

Fabrication assumptions: 2 layers, 1.6 mm FR-4, nominal 35 µm (1 oz) copper, green mask;
0.20 mm minimum tracks/clearance, 0.60/0.30 mm vias, 0.30 mm copper-to-edge
clearance, 0.12 mm mask web, and 1.0/0.15 mm minimum silk text height/stroke.
Confirm these, mask web capability, routed plated slots, and stencil
handling of the XIAO with the fabricator. The 42 × 24 mm measurement excludes
connector overhangs. There are no mounting holes; provide enclosure support.

Regenerate from the project root with KiCad 10 and its standard symbol, footprint,
and 3D-model libraries plus the `pcbnew` Python module:

```sh
bash scripts/export_rev2.sh
sha256sum -c hardware/rev2/checks/source-sha256.txt
```

The export script runs ERC, DRC/parity, the electrical/mechanical/model contract
check, and 20 regression tests before exporting production-format files. It never
overwrites `bom.csv`. Every purchasing identity/footprint mismatch stops the export;
all 12 identities now match. If the export
fails, do not use earlier output files as a release for the newly edited design.
The updated [review workflow](../../docs/automation.md) shares that validation
gate and generates a separate 2D preview; it does not publish this whole package.
Its build was tested locally in the pinned KiCad container. Actual GitHub-hosted
execution and Pages deployment have not been run here.

For JLCPCB, the normal handoff is a ZIP of `fabrication/` **including drills**,
the clean BOM, and a finalized centroid/CPL. See the [submission checklist](../../docs/jlcpcb.md#files-to-submit).
Do not submit `positions-front.csv` or the unmodified draft CPL as an approved CPL:
custom-part offsets/rotations and JLCPCB's placement preview still need review.

### Repeat the solid-clearance review

This optional audit uses OpenCascade, separately from the KiCad checks above.
After exporting, refresh its report in an isolated environment (verified here
with Python 3.14 and the pinned dependency):

```sh
cad_review_dir="$(mktemp -d -t hdmi2c-3d.XXXXXX)"
python3 -m venv "$cad_review_dir/venv"
"$cad_review_dir/venv/bin/pip" install -r scripts/requirements-3d.txt
"$cad_review_dir/venv/bin/python" scripts/check_rev2_3d.py hardware/rev2/assembly.step \
  --output hardware/rev2/checks/mechanical-3d.json
```

Reuse that environment for subsequent audits. The script checks XIAO-to-substrate
and XIAO-to-other-part solid intersections/distances, HDMI shell-to-substrate
interference, and the antenna's projection onto the carrier. It requires models
for all fitted parts and a current source manifest. It does not check solder,
cable plugs, enclosure, tolerances, or RF. Re-exporting the STEP changes its hash;
rerun this audit before citing an older report as current.
