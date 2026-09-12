# Source and license scope

This archive is Import Lens Free Preflight 1.0, an original Magta Assets checker. The complete archive is offered under MIT; this is a specific additional permissive grant for the included shared parser, not a change to the separate paid tool license.

`source/preflight.py` is copied byte-for-byte from the reviewed Import Lens 0.2 shared structure parser. Its historical module docstring and error messages retain the word “prototype”; they do not imply that the full paid engine workflow is included.

- Shared parser SHA-256: `442d3919f503bfe02748895633ea95eb5c41c1c2676a50ed70c41e2d12bb0c88`
- `check_glb.py` is a new free stdout-only wrapper.
- The wrapper’s 25 MiB cap, rates 30/60/120 and 4,000,000 source vertex/time workload formula match the paid 0.2 pre-import gate. The parser itself is not modified.
- Both example GLBs are the same original MIT calibration fixtures supplied with Import Lens 0.2. They have no textures, engine scripts or external resource dependencies.
- No paid import runner, Godot probe, import configuration script, optimizer comparison code or HTML renderer is included.

The shared static parser is not a complete glTF validator, image decoder or engine compatibility test. PREFLIGHT_PASS must not be relabeled “Godot compatible” or “good animation.” Actual imports, settings comparison and skin correspondence remain separate work.

AI assisted the original development, wrapper, documentation and tests. FILES_SHA256.txt identifies every other file in this archive.
