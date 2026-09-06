# PartDesignUpgrade

Extends the **PartDesign** workbench with four helpers:

- **Create Pipe** — sweep a parametric profile (circle, square, triangle,
  pentagon, hexagon, octagon) along a sketch or a set of edges. Supports
  rotation, offset, wall thickness (hollow pipe) and corner transitions,
  with a live preview. If the path belongs to a PartDesign body the pipe is
  added as an *additive* feature; otherwise a standalone parametric pipe is
  created.
- **Subtractive Pipe** — the same sweep but the profile is **removed** from
  the body (like a pocket following a path): a *subtractive* feature.
- **Assembly Cut** — cut several PartDesign bodies at once with a single
  sketch. For each body a linked *binder* (or an independent sketch copy) is
  created and a pocket applied automatically, one body after another.
- **Weight / Volume** — shows the volume (mm³ / cm³) and the mass of a body
  using a density picker (metals, plastics, wood, glass, concrete, ... or a
  custom value in kg/m³).

The four buttons are injected into the **Part Design Helper Features**
toolbar.

## Installation

Use the FreeCAD Addon Manager (Tools → Addon manager) and search for
*PartDesignUpgrade*, or clone this repository into your user Mod directory:

| FreeCAD | Location |
| --- | --- |
| 1.1+ on Windows | `%APPDATA%\FreeCAD\v1-1\Mod\PartDesignUpgrade` |
| 1.1+ on Linux | `~/.local/share/FreeCAD/Mod/PartDesignUpgrade` |
| 1.1+ on macOS | `~/Library/Application Support/FreeCAD/Mod/PartDesignUpgrade` |

## Usage

### Create Pipe / Subtractive Pipe
1. Select a sketch (or edges of a body) as the path.
2. Click **Create Pipe** (adds) or **Subtractive Pipe** (removes) in the
   Part Design Helper Features toolbar.
3. Set profile shape/size, rotation, offset and wall thickness — a live
   preview follows the values.
4. Click OK.

### Assembly Cut
1. Select a sketch that crosses the bodies to cut.
2. Click **Assembly Cut**.
3. Tick the target bodies (in cut order), choose *binder* (linked) or
   *independent copies*, click **Cut Bodies** and accept each pocket.

### Weight / Volume
1. Select a body (or any shape with volume).
2. Click **Weight / Volume** and pick the material density.

## Compatibility

FreeCAD >= 1.1.0 (PySide6).

## License

LGPL-2.1-or-later — see [LICENSE](LICENSE).