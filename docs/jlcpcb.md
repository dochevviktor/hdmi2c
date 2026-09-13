# JLCPCB preparation — rev2

Factory/part review 2026-09-12; J7 confirmation and verification 2026-09-13.
**CAD checks pass; the assembly order is not ready.**
All 12 fitted component identities are now matched. Assembler acceptance,
current availability, and the final placement file still require confirmation.
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

The user's [matching CSV](../hardware/rev2/bom.csv) is preserved except for the
explicit J7 correction below, based on the user's new selection on 2026-09-13.
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
| J7 | Würth 685119134923 / [C2930961](https://jlcpcb.com/partdetail/WurthElektronik-685119134923/C2930961) | Exact existing HDMI Type A socket; no footprint substitution |

The passive-component warnings compare engineering values such as `100k` with
MPN strings. Those warnings do not by themselves indicate an electrical mismatch;
the actual selected specifications above were reviewed. Manufacturer/MPN/LCSC
fields for all seven groups (12 components) are saved in the schematic
and PCB. Stock, price, quoted order quantities, and setup fees are not pinned or
guaranteed by this review; the CSV's commercial data is only the user's snapshot.

J7 is the [Würth 685119134923 HDMI receptacle](https://www.we-online.com/components/products/datasheet/685119134923.pdf).
The user's **C2930961** selection was confirmed against the JLCPCB listing above
and [LCSC's catalog](https://www.lcsc.com/product-detail/C2930961.html), both of
which identify this exact manufacturer part. The manufacturer's land pattern
matches the existing 19 pads at 0.50 mm pitch, 0.28 × 2.60 mm signal lands, and
14.50 mm shell-tab column spacing. No pad, slot, outline, route or 3D-model change
is required. Its catalog listing specifies Economic/Standard SMT assembly, but
the four plated-slot shell tabs still need explicit soldering-process confirmation.

The original auto-match, PI3HDMI1310-AZLEX / C516617, was a switching IC and remains
rejected. Only J7's row was manually corrected in the matching CSV. Its obsolete
IC pricing, stock/MOQ and account-quantity fields were cleared, not transferred
to the socket; the user's requested quantity of five was retained. Other rows
remain byte-identical. Export/validation scripts still never rewrite this input.

## Files and export safety

- `hardware/rev2/bom.csv`: user-managed JLCPCB matching snapshot, never overwritten
  by the export script.
- [bom-design.csv](../hardware/rev2/bom-design.csv): generated engineering BOM with
  specifications and purchasing fields; 12 fitted parts.
- [bom-jlcpcb-draft.csv](../hardware/rev2/bom-jlcpcb-draft.csv): clean, uniquely
  headed **draft** using MPNs as comments, expanded references, and quantities per
  board. All seven groups / 12 components have reviewed codes, including J7
  `685119134923` / `C2930961`. It remains a draft until assembly review is complete.
- [BOM audit](../hardware/rev2/checks/jlcpcb-bom.json): records source hashes and
  all 12 reviewed identities. `unresolved_references` is empty, but
  `ready_for_order` remains false until the separate assembly checks are complete.

The column format follows JLCPCB's [KiCad export guide](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad).
The existing `positions-front.csv` is still **raw KiCad placement data**, not an
approved JLCPCB CPL. U3 and J7 have non-centroid footprint origins. Before an order,
prepare and verify the CPL's offsets/rotations against JLCPCB's library/placement
preview, including pin 1, USB direction, and HDMI direction. Do not just relabel
the raw coordinate columns and assume the two custom parts will be placed correctly.

```sh
bash scripts/export_rev2.sh
sha256sum -c hardware/rev2/checks/source-sha256.txt
# Strict purchasing-identity check: now exits 0; this is not assembly approval.
python3 scripts/check_jlcpcb_bom.py hardware/rev2/bom.csv hardware/rev2/checks/netlist.xml \
  --report hardware/rev2/checks/jlcpcb-bom.json
```

Every purchasing identity/footprint mismatch now stops the main export; the old
J7 exception has been removed. Update purchasing fields and the reviewed part contract
together after approving a new selection. Re-export and refresh the separate
solid-check report as described in the [package README](../hardware/rev2/README.md).

## Files to submit

Yes: the normal JLCPCB handoff is **one fabrication ZIP plus a BOM and a CPL**.
Keep all three synchronized to the same reviewed design revision.

| Upload | Contents / current project file |
| --- | --- |
| Fabrication ZIP | ZIP the contents of `hardware/rev2/fabrication/`: copper, solder mask, silkscreen, paste, outline **and `.drl` drill files**. Keep the antenna cutout and HDMI plated-slot routing; drill-map PDFs and `.gbrjob` are supplementary. |
| BOM | Use the clean `hardware/rev2/bom-jlcpcb-draft.csv` for matching/review, not the duplicate-header `bom.csv` matching report. It now includes C2930961 and all 12 fitted parts; finalize the order only after assembly signoff. |
| Centroid / CPL / pick-and-place | Finalize from `hardware/rev2/positions-front.csv`, with `Designator,Mid X,Mid Y,Rotation,Layer`, mm units, and verified origin/rotation corrections. The current raw export is **not the finalized upload CPL**. |

This follows JLCPCB's [Gerber/drill guide](https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-9)
and [BOM/CPL guide](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad).
J7 is mixed SMT/plated-slot, so keep it in the placement list even though KiCad
marks the footprint through-hole. TP1–TP4 are etched test pads, not purchased parts.
No schematic or STEP upload is normally part of these three required file sets;
an assembly drawing or process note can support the XIAO/HDMI handling review.

File upload alone is not the final approval: select/confirm the two-layer 1.6 mm,
1 oz/green-mask board options and assembly service, check the Gerber preview and
part matches, and inspect placement orientation before paying. In particular,
verify USB direction, HDMI direction and pin 1, and agree on XIAO reflow handling
and soldering all four HDMI shell tabs. No files were submitted by this work.

## Assembly decisions still required

JLCPCB currently lists **10 × 10 mm minimum for Economic PCBA**, versus
**70 × 70 mm for Standard PCBA**; single-sided SMT/through-hole assembly is listed
for Economic. Thus this 42 × 24 mm carrier meets Economic's size requirement, but
that alone does not establish acceptance of these parts. Standard would require
a suitable larger panel/tooling arrangement. Their [assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
also distinguish tooling/fiducial requirements by service.

- [x] Resolve J7's exact catalog identity: Würth 685119134923 / C2930961.
- [ ] Confirm current J7 availability and explicitly include soldering its four
  plated-slot shell tabs, not just its SMT contacts.
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
groups, and **20 regression tests pass** (10 design, 8 BOM, 2 preview safety).
The [review workflow](automation.md) also passes the same checks in its pinned
KiCad 10.0.5 container. Nominal 3D clearances are unchanged and the separate
solid report now matches the current STEP/source hashes. This is CAD/purchasing
preparation, not JLCPCB DFM/DFA approval or a physical test.
