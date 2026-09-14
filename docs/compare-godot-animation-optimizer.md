# Check whether Godot’s animation optimizer changes your GLB

An animation looks different after import. Before changing several export settings at once, compare one setting using the same file and engine build.

Godot’s [4.5 Advanced Import Settings documentation](https://docs.godotengine.org/en/4.5/tutorials/assets_pipeline/importing_3d_scenes/advanced_import_settings.html#optimizer) explains that optimization reduces animation size and is normally worth keeping enabled. Disabling it is a diagnostic comparison when you suspect it affects a clip, not a universal fix.

## Start with an example you can reproduce

[Open the free antenna comparison](https://fufuufu.itch.io/import-lens-free-calibration). It plays two imports of the same original skinned GLB: optimization enabled and disabled. Select **SubtleCurve**, then **LinearControl**. Scrub both at the same time rather than comparing two independently playing videos.

You can also [download the Godot 4.5.1 project](https://github.com/reisaak/godot-animation-import-calibration/releases/download/v0.2.2-project/Import_Lens_Free_Calibration_Godot_4.5.1_v0.2.2-store.1.zip). Extract it and import its root `project.godot`. Keep both GLBs and their `.glb.import` sidecars: those sidecars carry the deliberate setting difference. Run the project after import finishes.

The supplied report records these results in Godot 4.5.1:

| Clip | Maximum sampled difference, file units | Keys: enabled / disabled |
| --- | ---: | ---: |
| SubtleCurve | 0.00189676474 | 160 / 242 |
| LinearControl | 0.000000406723 | 47 / 242 |

Both clips were sampled at 60 Hz, including the endpoints: 241 times and 1,024 imported vertices per time. These are recorded CPU-skinned positions, not a GPU measurement. The antenna uses metres, so the first difference is approximately 1.897 mm. Do not apply that conversion to a model with an unknown scale.

## Keep the comparison fair

Use the same GLB bytes and Godot executable for both imports. Keep the animation bake rate, root scale, skin settings and remaining options the same. The [Godot import configuration reference](https://docs.godotengine.org/en/4.5/tutorials/assets_pipeline/importing_3d_scenes/import_configuration.html) describes where these options live. Compare the same clip and time in each result.

If the rest mesh, vertex correspondence or skin binds differ, subtracting positions is not a valid optimizer-only comparison. A smaller key count alone also does not tell you whether the motion is acceptable. Judge a measured difference against the model’s scale, its closest camera view and the movement you need.

A clean result only describes the sampled times. It does not prove equivalence between samples, repair an animation or establish that optimizer-disabled output matches the original Blender animation perfectly.

## Check your own file for the supported workflow

The free Python checker reads a limited GLB subset without importing anything into Godot. From this repository’s root, with Python 3.11:

```sh
python3 preflight/check_glb.py preflight/examples/IL_Antenna.glb
python3 preflight/check_glb.py "/path/to/your-model.glb" --format json
```

The antenna returns `PREFLIGHT_PASS`: 1,024 split vertices, three joints, two four-second clips and an estimated 493,568 vertex/time pairs at 60 Hz. Read the [exit-status table and supported subset](../preflight/README.md) for your own file. `UNSUPPORTED` can simply mean the file exceeds this tool’s scope; it does not mean Godot cannot use it. `PREFLIGHT_PASS` does not certify a successful engine import or an animation-quality result.

## When the paid tool is useful

If your GLB fits that subset and you want to repeat the measurement on your own file, [Import Lens v0.2 is $5](https://saiasue36.gumroad.com/l/import-lens-godot-glb?utm_source=github&utm_medium=guide&utm_campaign=import_lens). It creates isolated imports, checks geometry and skin correspondence, and produces local HTML, JSON and Markdown reports. It requires Python 3.11 and the official stable Godot 4.5.1 or 4.7.2 executable; testing was on macOS.

The free project and checker remain usable without buying it. The paid runner is deliberately limited to a single skinned mesh and skin; it is not a repair tool or a general-purpose animation validator.
