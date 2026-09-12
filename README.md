# Godot animation import calibration

A small, original example for inspecting what Godot's animation optimizer changes. It shows the same skinned antenna imported twice, with optimization enabled and disabled, and a recorded comparison of the imported mesh positions.

## Getting started

- **In your browser:** [Open the free animation comparison](https://fufuufu.itch.io/import-lens-free-calibration).
- **In Godot 4.5.1:** [Download the ready-to-import project ZIP](https://github.com/reisaak/godot-animation-import-calibration/releases/download/v0.2.2-project/Import_Lens_Free_Calibration_Godot_4.5.1_v0.2.2-store.1.zip). Extract the ZIP into a new folder, then import its root `project.godot`.
- **Check your own GLB’s structure:** [Use the free Python preflight checker](preflight/README.md). It estimates the supported sampling workload without running Godot; a pass does not guarantee an engine import or measure animation quality.

The project ZIP opens directly in Godot. If you clone this repository instead, follow the `project/project.godot` instructions below.

For questions or reproducible problems, [open a GitHub issue](https://github.com/reisaak/godot-animation-import-calibration/issues).

The calibration project contains one model, two clips and a focused inspector. That inspector does not accept arbitrary files or provide an asset-quality score. The separate `preflight/` folder checks a local file’s static structure only.

## Run the included project

Use **Godot 4.5.1** to reproduce the recorded import behavior. Import `project/project.godot` into the Project Manager, allow the two GLBs to import, then run the project. Keep both `.glb.import` sidecars: they contain the deliberate optimization-setting difference.

With the Godot executable available as `godot`, the equivalent commands from the repository root are:

```sh
godot --headless --path project --import
godot --path project
```

Select a clip, play or scrub the synchronized models, and inspect the displacement display. The desktop project reserves a 52-pixel strip for the optional HTML navigation used by the web export. With the comparison focused, **Alt + Page Down / Alt + Page Up** scrolls it; the timeline keeps its ordinary Home/End controls.

`SubtleCurve` returns to its starting pose after four seconds. `LinearControl` is an intentionally non-looping ramp, so it jumps back when the inspector repeats it.

## What was measured

The recorded run used official Godot **4.5.1**, the same GLB bytes for both imports, matching rest geometry, skin weights, binds and hierarchy, and only the animation optimizer setting changed. Each clip was sampled at 60 Hz, including both endpoints: 241 poses and 1,024 corresponding imported vertices per pose.

| Clip | Maximum sampled difference, file units | Default / disabled animation keys |
| --- | ---: | ---: |
| SubtleCurve | 0.00189676474 | 160 / 242 |
| LinearControl | 0.000000406723 | 47 / 242 |

This particular model was authored in metres; the first difference is about 1.897 mm. The inspector's imported vertex count includes splits and differs from the editable mesh's 358 vertices. The editable model has 704 triangles and three bones.

These are sampled **CPU-skinned positions**, not a GPU readback. A difference or a smaller key count is not automatically a defect. Disabled optimization is a comparison baseline, not assumed source truth, and unmeasured times may have larger differences. The numbers describe this fixture and engine version, not other assets or Godot releases.

## Read the supplied report

`example-report.html` is one self-contained report for the included antenna. It needs no account, engine, server or file upload. Its controls select the clip, units and sample; both clips share chart axes. It does not analyze new files.

`report.html` presents the same result with navigation for the hosted demo. These are two presentations of one recorded dataset. The machine-readable inspector results are in `project/comparison.json`; `PROVENANCE.json` records the source and export provenance at package creation.

## Editable source

- `fixture/IL_Calibration.blend` — original model, materials, rig and two actions.
- `fixture/models/IL_Antenna.glb` — the reviewed source export.
- `fixture/fixture.json` — original positions, weights, formulas and export metadata.
- `fixture/source/build_fixture.py` — original Blender generator, created with Blender 4.5.13.
- `project/scripts/` — synchronized inspector, skin-point comparison and trace code.

The two GLBs inside `project/models/` are intentional identical copies with different import settings. They are not additional models. This repository includes no engine binary or paid import-and-comparison tool. The separate free preflight checker includes these antenna bytes and one original folded-ribbon GLB as small static-check examples.

For regeneration, work in a disposable copy and use Blender 4.5.13:

```sh
blender --background --python fixture/source/build_fixture.py
```

Regeneration writes the fixture's `.blend`, GLB and JSON. It does not automatically replace the two project copies or recompute the recorded comparison; keep the reviewed files if you want to reproduce the published example.

## Check a local GLB before an engine comparison

The separate [free preflight checker](preflight/README.md) needs Python 3.11 and no extra packages. From this repository’s root:

```sh
python3 preflight/check_glb.py "/path/to/your-model.glb"
```

It writes text or JSON to stdout and leaves the input unchanged. `PREFLIGHT_PASS` means the shared static structure checks and estimated sampling workload passed. Godot import, animation correspondence and quality remain untested. Read its small supported subset and exit-status table before interpreting a result. The paid runner, engine probes, optimizer comparison and report renderer are not included.

## Export the browser version

Install the official Godot 4.5.1 export templates. Create a `build` directory beside `project`, then export the included **Web Calibration** preset. It uses `shell.html`, Compatibility rendering and the single-thread web template.

```sh
mkdir -p build
godot --headless --path project --export-release "Web Calibration" ../build/index.html
```

Copy `report.html` into `build/` alongside the exported `index.html`. Keep the exported `index.*` names together and serve the build through a web host that supports Godot web exports. The report's return link restarts the comparison; **Back to downloads** opens the free example page. Generated engine/export files belong in `build/`, not in this source repository.

## License and provenance

The original calibration model and inspector use [CALIBRATION-LICENSE.txt](CALIBRATION-LICENSE.txt). That notice's original `inspector/` source is bundled here under `project/scripts/` with its scene and comparison resources. The separate web wrapper uses [WRAPPER-LICENSE.txt](WRAPPER-LICENSE.txt).

[CALIBRATION-REPORT-LICENSE.txt](CALIBRATION-REPORT-LICENSE.txt) grants MIT rights to the exact supplied example report and its navigation adaptation. Its original hash identifies `example-report.html`; it does not grant rights to the separate intake implementation. Preserve these notices when reusing their respective files. Godot's notices are included separately.

The files under `preflight/` have their own [MIT license](preflight/LICENSE.txt), including the unchanged shared parser, new wrapper and two original GLBs. That grant does not extend to the separate paid tool.

Created with AI assistance. The model, rig, animation formulas and example code are original. The editable Blender file's saved file-browser directory and render-output path were changed to relative paths for distribution; model data and evaluated animation poses were verified unchanged.
