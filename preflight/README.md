# Import Lens Free Preflight 1.0

Check whether a local skinned GLB passes Import Lens 0.2’s shared static structure checks before considering the paid comparison tool. Python 3.11 is the only requirement; no Godot installation or extra packages are needed.

A **PREFLIGHT_PASS is not an import guarantee or an animation-quality result**. This checker reads the file structure and estimates the requested sampling workload. It does not import into Godot, compare optimizer settings, verify imported geometry correspondence, render animation or repair anything. It is not a complete glTF validator.

## Run it

Extract the ZIP, open a terminal in `Import_Lens_Free_Preflight_v1.0`, and run:

```sh
python3 check_glb.py examples/IL_Antenna.glb
python3 check_glb.py "/path/to/your-model.glb" --format json
python3 check_glb.py "/path/to/your-model.glb" --sample-rate 30
```

Use `--help` for options or `--version` to confirm the launcher. Both examples should return PREFLIGHT_PASS at 30, 60 and 120. They are original calibration fixtures, not additional game assets.

Output goes to the terminal (stdout). The checker opens your input read-only and creates no output folders, reports, imports or Python caches. It runs no subprocesses and makes no network requests. JSON includes the input snapshot hash; errors do not include its full filesystem path. If you choose shell redirection yourself, use a separate output filename so you do not overwrite your GLB.

## What is checked

The unchanged shared parser accepts a deliberately limited subset: GLB 2 with one embedded buffer, one scene, one skinned mesh instance and one skin; triangle primitives; 1–64 joints, at most 256 nodes and 20,000 split vertices; four joint slots with float weights and explicit inverse bind matrices. One to eight uniquely named clips need joint TRS channels with LINEAR or STEP interpolation and positive end times no later than 30 seconds. Clip names use letters, digits, spaces, hyphens or underscores. Embedded PNG/JPEG resources are allowed by structure only; image content is not decoded or rendered.

External or data-URI resources, glTF extensions, morph targets, sparse accessors, multiple skins/mesh instances, extra influence sets, cubic interpolation and animated non-joint nodes are unsupported. A supported-subset rejection does **not** mean the file is unusable in Godot or another tool.

Files are limited to 25 MiB (26,214,400 bytes). `--sample-rate` accepts 30, 60 or 120; default 60. The pre-import workload estimate is exactly:

`sum((ceil(clip_end_seconds × sample_rate) + 1) × source_split_vertices)`

The selected estimate must not exceed 4,000,000. No positions are actually sampled. Imported vertex counts or clip identities may differ; later paid-tool checks can still reject a structurally passing file. For example, the shared parser accepts the simple name `RESET`, but the paid Godot stage reserves it. No engine-dependent eligibility is certified here.

## Read the result

| Result | Exit | Meaning |
| --- | ---: | --- |
| PREFLIGHT_PASS | 0 | Shared static checks and estimated workload passed; no engine or quality conclusion. |
| UNSUPPORTED | 2 | Outside this checker’s supported subset or resource limits; not necessarily a broken file. |
| MALFORMED | 3 | Header/structure/data failed a performed check; not a complete validation diagnosis. |
| INPUT_ERROR | 4 | File could not be read as a regular local GLB. |
| INPUT_CHANGED | 5 | Opened bytes changed during the check; retry a stable copy. |
| SETUP_ERROR | 6 | Python or included parser setup is incomplete. |

Invalid command-line arguments exit 64 and print usage to stderr. `--help` and `--version` exit 0 without inspecting a model. Each normal JSON result contains its status and explanation. The sample rate affects only the workload gate, not a measured result.

## Rights and scope

Everything in this **free checker archive** is MIT licensed. Keep LICENSE.txt with copies. This narrow grant includes the shared `source/preflight.py`, the original wrapper and the two GLBs; it does not relicense the separate paid import runner, engine probes, comparison or report renderer. None of those paid files is included here. Existing free Godot calibration projects are separate downloads.

Original code, fixtures and documentation were developed with AI assistance. See PROVENANCE.md for the exact shared-source identity. The checker was tested with standalone Python 3.11.15 on macOS; no other operating-system run is claimed.
