# PartDesignUpgrade

Extends the **PartDesign** workbench with seven helpers:

- **Create Pipe** — sweep a parametric profile (circle, square, triangle,
  pentagon, hexagon, octagon) along a sketch or a set of edges. Supports
  rotation, offset, wall thickness (hollow pipe) and corner transitions,
  with a live preview. If the path belongs to a PartDesign body the pipe is
  added as an *additive* feature; otherwise a standalone parametric pipe is
  created.
- **Subtractive Pipe** — the same sweep but the profile is **removed** from
  the body (like a pocket following a path): a *subtractive* feature.
- **Create Rib** — re-implements the **Rib** tool that was removed from
  PartDesign in FreeCAD 1.0: a stiffening plate is created from a sketch
  profile (open or closed wire) by extruding it *perpendicular to the sketch
  plane* by the requested thickness. Options: *midplane* (thickness split
  on both sides) and *reversed*. The rib is fused with the body as an
  *additive* feature.
- **Subtractive Rib** — same extrusion but **removed** from the body
  (a groove/channel following the sketch): a *subtractive* feature.
- **Create Rib Between Faces** — build a stiffening rib *without a sketch*:
  select **two faces** and a plate is created **between them**. Two **angled
  planar faces** (a corner) give a triangular gusset whose two long edges rest
  on the two faces (lengths measured from the corner edge; *Invert leg 1/2*
  flips each edge to the other side of the corner); a **planar face plus a
  cylinder** gives one or more radial plates running from the plane up to the
  cylinder (*Copies* rotates them around the cylinder axis, *Rotation angle*
  positions them). Triangle is the default profile, Rectangle also available.
  Added to the active body as an *additive* feature, or standalone when no
  body is active. A *Full face length* checkbox auto-sets the lengths and a
  static helper *sketch* of the rib profile is added to the document tree.
- **Assembly Cut** — cut several PartDesign bodies at once with a single
  sketch. For each body a linked *binder* (or an independent sketch copy) is
  created and a pocket applied automatically, one body after another.
- **Weight / Volume** — shows the volume (mm³ / cm³) and the mass of a body
  using a density picker (metals, plastics, wood, glass, concrete, ... or a
  custom value in kg/m³).

The six buttons are injected into the **Part Design Helper Features**
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

### Create Rib / Subtractive Rib
1. Select a sketch whose profile (open or closed wire) defines the rib.
   The sketch plane becomes the rib's mid-plane.
2. Click **Create Rib** (adds) or **Subtractive Rib** (removes).
3. Set the thickness (applied perpendicular to the sketch plane), enable
   *Midplane* to split it on both sides, or *Reversed* to flip the normal
   direction — a live preview follows the values.
4. Click OK.

### Assembly Cut
1. Select a sketch that crosses the bodies to cut.
2. Click **Assembly Cut**.
3. Tick the target bodies (in cut order), choose *binder* (linked) or
   *independent copies*, click **Cut Bodies** and accept each pocket.

### Create Rib Between Faces
1. Select **two faces** — two angled planar walls (corner), or a planar face
   plus a cylinder.
2. Click **Create Rib Between Faces**.
3. Corner: set *Length 1* / *Length 2* (contact lengths from the corner edge),
   *Thickness*, *Offset* (slide along the corner edge), *Invert leg 1* /
   *Invert leg 2* (flip a leg to the other side of the corner) and *Copies*
   with *Spacing* for a pattern — a triangular gusset closes the angle
   (Triangle is the default profile).
4. Plane + cylinder: set *Length 1* (height up the cylinder), *Length 2*
   (radial contact on the plane), *Thickness*, *Copies* (radial pattern) and
   *Rotation angle* (Triangle is also the default profile here).
5. Tick **Full face length** to make the lengths automatically cover the whole
   faces (un-tick to edit them manually again).
6. Click OK. A helper *sketch* showing the rib profile is created in the
   document tree next to the rib feature — it is a static snapshot, not
   parametric.

### Weight / Volume
1. Select a body (or any shape with volume).
2. Click **Weight / Volume** and pick the material density.

## Compatibility

FreeCAD >= 1.1.0 (PySide6).

## License

LGPL-2.1-or-later — see [LICENSE](LICENSE).