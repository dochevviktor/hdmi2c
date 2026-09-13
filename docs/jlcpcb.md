# JLCPCB preparation — rev2

Factory/part review 2026-09-12; automation verification 2026-09-13.
**CAD checks pass; the assembly order is not ready.**
J7 sourcing, assembler acceptance, and the final placement file remain unresolved.
No files were uploaded, no parts reserved, and no order placed.

## Template and board settings

The carrier really is **two copper layers**, 42 × 24 mm, nominal 1.6 mm FR-4.
The user-supplied `kicad_templates-master.zip` was extracted and its
`JLCPCB_1-2Layer` directory reviewed. This is a **KiCad 5 / 2019** snapshot,
archive commit `7a393457f57f22cc15bf484340ad554363761557`. Despite its name, both
its PCB and `.pro` file enable **four** copper layers (`CopperLayerCount=4`).
Its layer table, worksheet, legacy plot options, and whole project file were
therefore not imported into the working KiCad 10 design.

Archive SHA-256:

```text
9e39d52f667d11d42a962d5fce8701ad84b1f88ab81b73f83aa69e36a29d241f
```

The applied profile assumes **1 oz copper and green solder mask**. Other colors,
copper weights, finishes, or processes need a fresh review. These are local CAD
settings, not options already selected in a JLCPCB order.

| Setting, mm unless stated | Supplied template | Applied rev2 profile |
| --- | ---: | ---: |
| Copper layers | 4 (inconsistent with folder name) | 2, retained |
| Board thickness | 1.6002 | 1.6, retained |
| Minimum track / copper clearance | 0.127 / 0.127 | 0.20 / 0.20, retained |
| Minimum via diameter / drill | 0.60 / 0.30 | 0.60 / 0.30 |
| Minimum via annular width | Implicit 0.15 for default via | 0.15 |
| Minimum hole-to-hole clearance | 0.40 | 0.45, conservatively applied to all holes |
| Minimum hole-to-copper clearance | Not explicit | 0.28, conservatively applied globally |
| Copper-to-routed-edge clearance | Not explicit | 0.30, retained |
| Mask expansion / minimum web | 0 / 0.12 | 0 / 0.12 |
| Mask opening to neighboring copper | Not explicit | 0.09 |
| Minimum silkscreen text height / stroke | Defaults 0.8128 / 0.1524 | Constraints 1.0 / 0.15 |
| Silkscreen clearance | Not explicit | 0.15 |

Compared with JLCPCB's [current fabrication capabilities](https://jlcpcb.com/capabilities/pcb-capabilities):
the retained track/via choices have margin; current mask guidance permits 1:1
openings. Component PTH rings have a different requirement from via rings: the
HDMI shell lands were retained, not reduced to the via minimum. The antenna notch
and plated slots are routed features; this is not a V-scored panel.

Updated routing presets are 0.20/0.40/0.60/1.00 mm tracks and 0.60/0.30,
0.90/0.40 mm vias. Blind/buried vias and microvias remain disabled. Solder paste
expansion remains zero; vias remain tented, not specified as epoxy-filled.

The tighter checks initially found 38 silkscreen text/spacing issues. Enlarged
text, moved U4/SW2/SW3/TP references, and increased 33 footprint silkscreen
graphic strokes from 0.12 to 0.15 mm. The latter are PCB-instance styling changes;
refreshing standard footprints can reset them, so a regression check now guards
their minimum width. **Pads, traces, vias, component locations, outline, and
electrical connectivity were not changed.** No DRC exclusions or severity
reductions were used. Existing unrelated project preferences were preserved.

## Part selections

The user's [matching CSV](../hardware/rev2/bom.csv) is preserved byte-for-byte.
Its duplicate `JLCPCB Part #` headers contain an empty input column and a populated
selected-part column; it also contains multiline descriptions and ranged
designators. It is a matching report, **not the clean upload BOM**.

| References | Manufacturer part / selected code | Review |
| --- | --- | --- |
| U3 | Seeed 113991254 / [C27675191](https://jlcpcb.com/partdetail/Seeed-113991254/C27675191) | Complete XIAO ESP32-C6; module handling/reflow and placement still need JLCPCB confirmation |
| U4 | TI TPD12S016PWR / [C201665](https://jlcpcb.com/partdetail/TexasInstruments-TPD12S016PWR/C201665) | Correct PW/TSSOP-24 part, not RKT/UQFN |
| SW2, SW3 | Omron B3U-1000P / [C231329](https://jlcpcb.com/partdetail/OmronElectronics-B3U1000P/C231329) | Matches the existing switch |
| R24, R25 | FOJAN FRH0603B1003TS / [C51048211](https://jlcpcb.com/partdetail/FOJAN-FRH0603B1003TS/C51048211) | 100 kΩ, 0.1 W, ±0.1%, 0603; meets design requirements |
| R26, R27 | Sunway SC0603F1002F2BNRH / [C3152123](https://jlcpcb.com/partdetail/Sunway-SC0603F1002F2BNRH/C3152123) | 10 kΩ, 0.1 W, ±1%, 0603; meets requirements |
| C1–C3 | YAGEO CC0603KRX7R9BB104 / [C14663](https://jlcpcb.com/partdetail/YAGEO-CC0603KRX7R9BB104/C14663) | 100 nF, 50 V, X7R, ±10%, 0603; exceeds the minimum 16 V requirement |
| J7 | Selected PI3HDMI1310-AZLEX / C516617 | **Rejected: an IC, not a connector** |

The passive-component warnings compare engineering values such as `100k` with
MPN strings. Those warnings do not by themselves indicate an electrical mismatch;
the actual selected specifications above were reviewed. Manufacturer/MPN/LCSC
fields for the six suitable groups (11 components) are saved in the schematic
and PCB. Stock, price, quoted order quantities, and setup fees are not pinned or
guaranteed by this review; the CSV's commercial data is only the user's snapshot.

J7 requires the [Würth 685119134923 HDMI receptacle](https://www.we-online.com/components/products/datasheet/685119134923.pdf).
The selected [PI3HDMI1310-A](https://www.diodes.com/part/view/PI3HDMI1310-A) is a
72-contact HDMI switching IC and cannot fit or replace it. No verified JLCPCB
catalog code for the exact Würth connector was found in this review. Retain the
socket pending a choice between sourcing/consignment through JLCPCB, hand-fitting
it after delivery, or reviewing a stocked connector and any required footprint
redesign. None of those choices has been executed.

## Files and export safety

- `hardware/rev2/bom.csv`: user-managed JLCPCB matching snapshot, never overwritten
  by the export script.
- [bom-design.csv](../hardware/rev2/bom-design.csv): generated engineering BOM with
  specifications and purchasing fields; 12 fitted parts.
- [bom-jlcpcb-draft.csv](../hardware/rev2/bom-jlcpcb-draft.csv): clean, uniquely
  headed **draft** using MPNs as comments, expanded references, and quantities per
  board. J7 remains present with its correct MPN and a blank LCSC code. It is not
  silently omitted or assigned the incorrect IC.
- [BOM audit](../hardware/rev2/checks/jlcpcb-bom.json): records source hashes and
  the unresolved/rejected J7 mapping. `ready_for_order` remains false.

The column format follows JLCPCB's [KiCad export guide](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad).
The existing `positions-front.csv` is still **raw KiCad placement data**, not an
approved JLCPCB CPL. U3 and J7 have non-centroid footprint origins. Before an order,
prepare and verify the CPL's offsets/rotations against JLCPCB's library/placement
preview, including pin 1, USB direction, and HDMI direction. Do not just relabel
the raw coordinate columns and assume the two custom parts will be placed correctly.

```sh
bash scripts/export_rev2.sh
sha256sum -c hardware/rev2/checks/source-sha256.txt
# Strict purchasing check: currently exits 1 because J7 is unresolved.
python3 scripts/check_jlcpcb_bom.py hardware/rev2/bom.csv hardware/rev2/checks/netlist.xml \
  --report hardware/rev2/checks/jlcpcb-bom.json
```

The main export explicitly permits only the known J7 blocker to produce a draft;
other mismatches stop it. Update purchasing fields and the reviewed part contract
together after approving a new selection. Re-export and refresh the separate
solid-check report as described in the [package README](../hardware/rev2/README.md).

## Assembly decisions still required

JLCPCB currently lists **10 × 10 mm minimum for Economic PCBA**, versus
**70 × 70 mm for Standard PCBA**; single-sided SMT/through-hole assembly is listed
for Economic. Thus this 42 × 24 mm carrier meets Economic's size requirement, but
that alone does not establish acceptance of these parts. Standard would require
a suitable larger panel/tooling arrangement. Their [assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
also distinguish tooling/fiducial requirements by service.

- [ ] Resolve J7 sourcing and explicitly include soldering its four plated-slot
  shell tabs, not just its SMT contacts.
- [ ] Have JLCPCB confirm placement and the soldering profile for the **complete
  XIAO module**; a catalog listing is not approval of this custom carrier mounting.
- [ ] Confirm Economic versus Standard, actual component availability, finish,
  stencil, handling of the notched outline/overhanging connectors, and any panel,
  rails, fiducials, or tooling holes. Do not enlarge the carrier just to match the
  Standard minimum without choosing that process first.
- [ ] Finalize and inspect the CPL and JLCPCB placement preview before paying.
- [ ] Perform the existing physical fit, power, USB, RF, and monitor checks.

The carrier itself has no castellated edge holes: the castellations belong to
the purchased XIAO. Do not select special carrier edge-plating/castellation
fabrication solely because the module uses castellated mounting.

Validation: KiCad 10.0.6 ERC/DRC/parity/unrouted **0 findings**, 38 matching pin
groups, and **18 regression tests pass** (10 design, 6 BOM, 2 preview safety).
The [review workflow](automation.md) also passes the same checks in its pinned
KiCad 10.0.5 container. Nominal 3D clearances are unchanged and the separate
solid report now matches the current STEP/source hashes. This is CAD/purchasing
preparation, not JLCPCB DFM/DFA approval or a physical test.
