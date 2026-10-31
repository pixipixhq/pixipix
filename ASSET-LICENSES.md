# Asset licenses

This file is the authoritative rights statement and distribution manifest for visual
assets in the PixiPix repository.

## Restricted distribution paths

The paths in this delimited block are repository-only directory prefixes. Release tooling
reads the block directly and rejects any wheel or source-distribution member beneath them.

<!-- pixipix:restricted-distribution-paths:start -->
    assets/brand/
    examples/pixi-demo/
<!-- pixipix:restricted-distribution-paths:end -->

The currently tracked reserved assets include:

```text
assets/brand/pixipix-logo.png
assets/brand/pixipix-mascot-logo.png
assets/brand/pixi-before-after.png
assets/brand/pixi-aligned-frames.png
examples/pixi-demo/pixi-demo-sheet.png
examples/pixi-demo/** (source and derived images containing Pixi)
```

## Pixi mascot asset rights

These assets are not distributed under Apache-2.0. They remain visible in a public
repository checkout so users can inspect the flagship example and run it locally.
Repository visibility does not grant permission for standalone redistribution, unrelated
modification, reuse, or incorporation into another project.

Users may copy and process the source sheet locally to exercise the example. Generated
Pixi frames retain the same reserved status as the source artwork. Wheels and source
distributions exclude every restricted distribution path above.

The before-and-after and aligned-frame previews are derived from the Pixi demo's
actual extracted and aligned CLI output. Their checkerboard backgrounds are display
aids; the previews and the Pixi artwork they contain remain reserved.

Historical note: `assets/pixipix-logo.png` was inadvertently included in the published
`0.1.0a4` source distribution. Future distributions exclude reserved brand assets. This
notice grants no additional rights in previously published copies.

## Reusable geometric example

`examples/geometric-demo/` contains Apache-2.0-licensed geometric artwork,
configuration, and documentation. Its source image and configuration are copied
from the repository's original synthetic fixtures. Its derived geometric frames
are also covered by Apache-2.0. See the
[example's license and provenance](examples/geometric-demo/README.md#license-and-provenance).
This example contains no Pixi artwork and is permitted in source distributions.
