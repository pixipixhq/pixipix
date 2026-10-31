# Reusable geometric example

Two small geometric robots demonstrate the complete pipeline without reserved artwork.
The source image and configuration are exact copies of
[`robot-geometric.png`](../../tests/fixtures/robot-geometric.png) and
[`robot-geometric.toml`](../../tests/fixtures/robot-geometric.toml).

## Run

Install PixiPix using Python 3.12:

```bash
pip install pixipix
```

Or install it as an isolated tool with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install --python 3.12 pixipix
```

Download `source.png` and `pixipix.toml` from this directory into the same local
directory, then run these commands there:

```bash
pixipix inspect source.png --config pixipix.toml
pixipix run source.png --config pixipix.toml --output build/geometric-demo
```

From a repository checkout, you can instead run:

```bash
uv run pixipix run examples/geometric-demo/source.png \
  --config examples/geometric-demo/pixipix.toml \
  --output build/geometric-demo
```

## Expected result

- Inspection accepts two components, named `idle` and `signal`.
- The run creates `extract/`, `scale/`, `pixelize/`, and `align/` stage directories.
- Final frames are `build/geometric-demo/align/frames/idle.png` and `signal.png`.
- Both final images are transparent RGBA PNGs, exactly **4×4 pixels**. Enlarge them
  with nearest-neighbor scaling to inspect the pixels.
- There are no warnings or clipping findings. Stage metadata records the frame
  order, dimensions, and placement.

Choose a new output directory for another run, or pass `--force` to replace an
existing output that PixiPix verifies it owns.

## License and provenance

This example's source image, configuration, documentation, and derived geometric
frames are covered by the repository's [Apache-2.0 license](../../LICENSE).
You may reuse and modify them under that license.

The source is original, programmatically drawn geometric test data created for
PixiPix by the repository owner in 2026. It contains no third-party or AI-generated
artwork. See the [fixture provenance](../../tests/fixtures/README.md) and
[generator](../../tests/fixtures/generate_fixtures.py).

The **Pixi mascot and its previews are separate, reserved artwork**. Their
[asset rights](../../ASSET-LICENSES.md) do not apply to these geometric robots.
