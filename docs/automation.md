# Rev2 review automation

Updated 2026-09-13. The [workflow](../.github/workflows/main.yml) builds a **CAD
review preview**, not an approved fabrication/assembly package. A green run does
not resolve the [JLCPCB placement and assembly checks](jlcpcb.md).

## What runs

Pushes to `main`, pull requests targeting `main`, and manual workflow runs:

1. Use the official KiCad **10.0.5** container, pinned by digest, and
   InteractiveHtmlBom **2.12.0**, pinned by commit. The official registry did not
   yet have 10.0.6; local CAD work uses 10.0.6. Both were tested below.
2. Run `scripts/validate_rev2.sh`: ERC, DRC/parity/unrouted checks, the 38-group
   electrical contract, footprint/model/keepout/silk checks, and 20 regression
   tests (10 design, 8 purchasing, 2 preview-output safety tests).
3. Audit the matching CSV without changing it. All 12 fitted part identities
   must match; the former J7 exception is removed after confirming C2930961.
4. Generate an interactive BOM, schematic PDF, engineering BOM, clearly named
   JLCPCB draft BOM, and reports into a **new** `out/` directory. J7 retains its
   correct socket MPN with C2930961. Test pads do not count as fitted parts.
5. Retain diagnostics even after a failed check. Upload a review preview only
   after a successful build. Upload/deploy Pages **only from `main`, never from a
   pull request**. A manual run on another branch produces a preview only.

The build token has read-only repository permissions and checkout credentials
are not persisted. Only the separate deploy job has Pages/OIDC write permissions.
Pull-request builds can cancel superseded PR builds; Pages deployments are serialized.
No workflow was dispatched, pushed, or deployed during this local work. Actual
GitHub-hosted execution and the repository's Pages/environment settings remain to
be verified by the owner after committing/pushing the changes.

## What is deliberately excluded

The site does not copy `hardware/rev2/` wholesale. It excludes the raw user matching
CSV, Gerbers, raw placements/CPL, STEP files and 3D renders. The supplied model's
[redistribution caveat](../3d/README.md) is unchanged. CI neither refreshes nor
claims to run the optional OpenCascade solid audit; it only checks the pinned
local model and its CAD transform as part of the regular design contract.

The full prototype exporter still uses `scripts/export_rev2.sh`. Its validation
gate is now shared with CI, and it still never overwrites `hardware/rev2/bom.csv`.
The [separate solid audit](../hardware/rev2/README.md#repeat-the-solid-clearance-review)
must be rerun after exporting new STEP geometry. A review site is not a substitute
for that package or for physical hardware tests.

## Local preview

With KiCad 10, its standard symbol/footprint libraries and `pcbnew` Python module
installed, run from the project root:

```sh
preview_dir="$(mktemp -d -t hdmi2c-preview.XXXXXX)"
git clone --no-checkout https://github.com/openscopeproject/InteractiveHtmlBom.git \
  "$preview_dir/InteractiveHtmlBom"
git -C "$preview_dir/InteractiveHtmlBom" checkout --detach \
  5c192e794cd66fde04bab11810601b711bf8581b
bash scripts/build_review_site.sh "$preview_dir/InteractiveHtmlBom" "$preview_dir/site"
# Open the generated site/index.html in a browser.
```

The builder refuses an existing output directory rather than deleting it or
mixing in stale assets. Choose a new path on each run. An export failure may leave
partial diagnostics there, but CI will not upload it as a successful site.
To run checks without building a site:

```sh
validation_dir="$(mktemp -d -t hdmi2c-checks.XXXXXX)"
bash scripts/validate_rev2.sh "$validation_dir"
```

## Verification and dependency provenance

- Complete headless preview builds passed locally on KiCad 10.0.6 and in the
  **exact pinned 10.0.5 container**, with a read-only project mount and networking
  disabled for the container build. Both returned zero ERC/DRC/parity/unrouted
  findings, 38 matching pin groups, and 20 passing tests.
- Inspected the generated interactive BOM in Firefox: 7 groups / 12 fitted parts,
  four test pads excluded, correct J7 socket MPN and C2930961 purchasing code.
  All review-index links resolve. Strict identity checking exits 0; the old
  incorrect IC snapshot still fails. Assembly approval remains separate.
- `actionlint` 1.7.12, ShellCheck, shell syntax and whitespace checks pass. These
  local checks do not test GitHub authentication, artifact uploads or deployment.
- The matching CSV's J7 row was explicitly corrected on the user's selection of
  C2930961; all other rows are unchanged. Export scripts never rewrite it.
  The current digest is recorded in `hardware/rev2/checks/source-sha256.txt`.

The removed upstream generator [installs KiCad 6](https://github.com/wlcx/kicad-site-generator/blob/main/Dockerfile).
The replacement uses [KiCad's official container distribution](https://www.kicad.org/download/docker/)
and [InteractiveHtmlBom 2.12.0](https://github.com/openscopeproject/InteractiveHtmlBom/releases/tag/v2.12.0).
Official actions are pinned to verified release commits: [checkout 7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1),
[upload-artifact 7.0.1](https://github.com/actions/upload-artifact/releases/tag/v7.0.1),
[upload-pages-artifact 5.0.0](https://github.com/actions/upload-pages-artifact/releases/tag/v5.0.0),
and [deploy-pages 5.0.1](https://github.com/actions/deploy-pages/releases/tag/v5.0.1).
Dependency updates require a new preview build and review; none floats on `main`.
