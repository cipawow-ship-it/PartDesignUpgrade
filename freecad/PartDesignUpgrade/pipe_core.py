# -*- coding: utf-8 -*-
import math
import time

import FreeCAD
import Part

try:
    from .translations import tr as _tr
except ImportError:
    from translations import tr as _tr


# =============================================================================
# Helpers for the pipe sweep
# =============================================================================

_CORNER_MODES = {"Right corner": 1, "Round corner": 2, "Transformed": 0}

_WARN_STATE = {"key": "", "stamp": 0.0}


def _warn_throttled(msg, cooldown=3.0):
    """Print a console warning at most once per *cooldown* seconds per message.

    The pipe preview recomputes on every spinbox tick while the user drags a
    value, so an unthrottled warning floods the console with identical lines.
    """
    now = time.time()
    if msg == _WARN_STATE["key"] and now - _WARN_STATE["stamp"] < cooldown:
        return
    _WARN_STATE["key"] = msg
    _WARN_STATE["stamp"] = now
    FreeCAD.Console.PrintWarning(msg)


def _build_frame(tangent):
    """Return two orthonormal vectors spanning the plane perpendicular to tangent."""
    axes = [FreeCAD.Vector(1, 0, 0), FreeCAD.Vector(0, 1, 0), FreeCAD.Vector(0, 0, 1)]
    ref = min(axes, key=lambda a: abs(a.dot(tangent)))
    n1 = (ref - tangent * ref.dot(tangent))
    if n1.Length < 1e-9:
        n1 = FreeCAD.Vector(1, 0, 0)
    n1.normalize()
    n2 = tangent.cross(n1).normalize()
    return n1, n2


def _frame_rotation(n1, n2, tan):
    """Rotation whose local X/Y/Z axes map to *n1*/*n2*/*tan*.

    Used to orient the native profile plane so its X/Y match the preview
    frame from _build_frame; otherwise polygons come out rotated.
    """
    t = FreeCAD.Vector(tan)
    if t.Length > 1e-9:
        t.normalize()
    r0 = FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), t)
    x0 = r0.multVec(FreeCAD.Vector(1, 0, 0))
    ang = math.atan2(t.dot(x0.cross(n1)), x0.dot(n1))
    return FreeCAD.Rotation(t, math.degrees(ang)).multiply(r0)


def _path_tangent(wire):
    """Unit tangent direction at the start of a path wire."""
    for e in wire.OrderedEdges:
        p0 = e.FirstParameter
        p1 = e.LastParameter
        if p1 - p0 <= 1e-9:
            continue
        start = e.Vertexes[0].Point
        delta = (e.valueAt(p0 + (p1 - p0) * 0.01) - start)
        if delta.Length > 1e-9:
            return delta.normalize()
    return None


def _offset_from_dialog(tan, lateral, vertical):
    """Map the dialog (lateral >= 0, vertical signed) onto the global offset vector."""
    vz = FreeCAD.Vector(0, 0, 1)
    up = vz - tan * vz.dot(tan)
    if up.Length < 1e-9:
        n1, _n2 = _build_frame(tan)
        up = n1
    up.normalize()
    side = up.cross(tan)
    if side.Length < 1e-9:
        side = FreeCAD.Vector(1, 0, 0).cross(tan)
    side.normalize()
    return side * lateral + up * vertical


def _profile_points(ptype, dim, center, n1, n2, rotation=0.0):
    """Return polygon points for a regular-polygon profile centered on the plane."""
    sides = {
        "Square": 4,
        "Triangle": 3,
        "Pentagon": 5,
        "Hexagon": 6,
        "Octagon": 8,
    }.get(ptype)
    if sides is None:
        return None
    if ptype == "Square":
        rotation += math.pi / 4.0
    R = dim / (2.0 * math.sin(math.pi / sides))
    pts = []
    for k in range(sides):
        ang = 2.0 * math.pi * k / sides + rotation
        pts.append(center + n1 * (R * math.cos(ang)) + n2 * (R * math.sin(ang)))
    pts.append(pts[0])
    return pts


def build_pipe_from_wire(wire, profile_type, dimension, rotation=0.0, offset=None, transition=1, wall_thickness=0.0):
    """Build a solid sweeping a profile along a path wire.

    The profile is placed perpendicular to the path at its first vertex and
    rotated around the path axis by *rotation* radians. *transition* selects
    the corner handling at path kinks (1 = Right, 2 = Round, 0 = Transformed),
    as in FreeCAD's "Corner transition". Uses BRepOffsetAPI_MakePipeShell
    (same as PartDesign). *wall_thickness* (default 0, solid): when > 0 the
    pipe is hollow; *dimension* is the EXTERNAL size and a second, smaller
    profile is swept and subtracted.
    """
    if wire is None or wire.isNull():
        raise ValueError("The path is empty")

    d = float(dimension)
    if d <= 0:
        raise ValueError("The profile dimension must be positive")
    wt = 0.0
    try:
        wt = float(wall_thickness or 0.0)
    except (TypeError, ValueError):
        wt = 0.0

    tan = _path_tangent(wire)
    if tan is None:
        raise ValueError("Could not determine the direction of the path")

    center = wire.OrderedEdges[0].Vertexes[0].Point + (offset or FreeCAD.Vector(0, 0, 0))
    n1, n2 = _build_frame(tan)

    def _sides():
        return {"Square": 4, "Triangle": 3, "Pentagon": 5, "Hexagon": 6, "Octagon": 8}.get(profile_type)

    def _area(dim):
        if profile_type == "Circle":
            return math.pi * dim * dim
        sides = _sides()
        return sides * (dim * dim) / (4.0 * math.tan(math.pi / sides))

    def _volume_ratio(result, dim):
        """Fraction of the expected volume actually swept (0.0..1.0)."""
        if result is None or result.isNull() or not result.isValid():
            return 0.0
        path_len = wire.Length
        if path_len <= 0.0:
            return 0.0
        expected = _area(dim) * path_len
        if expected <= 0.0:
            return 0.0
        return result.Volume / expected

    def _make(dim, rotation, only_mode=None):
        if profile_type == "Circle":
            circle = Part.Circle(center, tan, dim)
            profile = Part.Wire(circle.toShape())
        else:
            pts = _profile_points(profile_type, dim, center, n1, n2, rotation)
            if pts is None:
                raise ValueError("Unknown profile type: {}".format(profile_type))
            profile = Part.makePolygon(pts)

        if only_mode is not None:
            modes = [only_mode]
        else:
            modes = [transition] + [t for t in (0, 1, 2) if t != transition]
        for t in modes:
            shell = wire.makePipeShell([profile], True, True, t)
            if not (shell.isValid() and not shell.isNull()):
                shell = wire.makePipeShell([profile], True, False, t)
            if shell.isValid() and not shell.isNull() and _volume_ratio(shell, dim) >= 0.5:
                return shell, t
        return None, transition

    def _sweep(dim, rotation, only_mode=None):
        """Sweep *dim* along the wire at the exact requested rotation.

        The cross-section orientation is never changed: it stays exactly what
        the user asked for. If OCCT cannot build the bend with the chosen
        corner transition, the other transition modes are tried at the same
        rotation (the caller is told which one was actually used). Sweeps that
        stay badly truncated or degenerate are rejected with an error instead
        of producing a broken pipe.
        """
        shp, used_mode = _make(dim, rotation, only_mode)
        if shp is None:
            return None, rotation, used_mode
        ratio = _volume_ratio(shp, dim)
        if ratio < 0.75:
            _warn_throttled(
                _tr("Pipe sweep truncated on this path (volume {:.1f}, "
                    "expected ~{:.1f}). Reduce the profile size or offset, or "
                    "round the path corners.").format(shp.Volume, _area(dim) * wire.Length) + "\n")
        return shp, rotation, used_mode

    def _inner_dimension(t):
        """Dimension of the inner profile for a wall of thickness *t*."""
        if wt <= 0:
            return 0.0
        if profile_type == "Circle":
            return d - t
        sides = _sides()
        apothem = d / (2.0 * math.tan(math.pi / sides))
        inner_apothem = apothem - t
        if inner_apothem <= 0:
            return 0.0
        return 2.0 * inner_apothem * math.tan(math.pi / sides)

    outer, _, outer_mode = _sweep(d, rotation)
    if outer is None:
        raise ValueError(_tr(
            "Could not sweep the profile along the path (degenerate result). "
            "Try changing the profile size or smoothing the path corners."))

    _MODE_NAMES = {0: "Transformed", 1: "Right corner", 2: "Round corner"}
    if _MODE_NAMES.get(outer_mode, "") != _MODE_NAMES.get(transition, ""):
        _warn_throttled(
            _tr("Note: corner transition '{}' is not possible at this profile "
                "rotation; using '{}' (profile rotation left unchanged).").format(
                _MODE_NAMES.get(transition, str(transition)),
                _MODE_NAMES.get(outer_mode, str(outer_mode))) + "\n")

    if wt <= 0:
        return outer

    inner_dim = _inner_dimension(wt)
    if inner_dim <= 0:
        FreeCAD.Console.PrintWarning(
            _tr("Wall thickness too large for the profile: keeping a solid pipe.") + "\n")
        return outer
    inner, _, _ = _sweep(inner_dim, rotation, only_mode=outer_mode)
    if inner is None:
        return outer
    try:
        hollow = outer.cut(inner)
        if hollow is not None and not hollow.isNull() and hollow.isValid() and hollow.Volume > 0:
            proj_area = _area(d) - _area(inner_dim)
            if hollow.Volume >= proj_area * wire.Length * 0.7:
                return hollow
            return outer
    except Exception:
        return outer
    return outer


# =============================================================================
# Native PartDesign pipe (AdditivePipe / SubtractivePipe)
# =============================================================================

_POLY_SIDES = {"Square": 4, "Triangle": 3, "Pentagon": 5, "Hexagon": 6, "Octagon": 8}


def _load_profile_lib():
    """Return the module exposing makeRegularPolygon (FreeCAD's sketcher lib)."""
    from ProfileLib import RegularPolygon
    return RegularPolygon


def _build_fc_profile(sk, ptype, dim, rot_deg=0.0):
    """Draw a fully constrained profile in a sketch's local plane.

    The profile is the 'pipe cross-section': a circle (radius = *dim*) or a
    regular polygon (side = *dim*). Polygons are built with the standard
    sketcher construction (inscribed in a construction circle) via
    ProfileLib.RegularPolygon, then fully constrained with:

      - construction circle radius (drives the size),
      - centre distances from the sketch origin (X and Y),
      - one horizontal distance of the first corner (drives the rotation;
        the corner already sits on the circle, so a second vertical distance
        would be redundant).

    *rot_deg* rotates the cross-section around the pipe axis (the sketch
    normal).
    """
    import math as _math

    from Sketcher import Constraint  # noqa: PLC0415

    if ptype == "Circle":
        sk.addGeometry(Part.Circle(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), dim))
        sk.Document.recompute()
        sk.addConstraint(Constraint("Radius", 0, dim))
        sk.Document.recompute()
        sk.addConstraint(Constraint("DistanceX", 0, 3, 0.0))
        sk.Document.recompute()
        sk.addConstraint(Constraint("DistanceY", 0, 3, 0.0))
        sk.Document.recompute()
        return

    sides = _POLY_SIDES.get(ptype)
    if sides is None:
        raise ValueError("Unknown profile type: {}".format(ptype))

    rot = _math.radians(rot_deg)
    if ptype == "Square":
        # mirror _profile_points: the preview draws the square with its
        # corners at 45 deg so that *dim* is the side length
        rot += _math.pi / 4.0
    R = dim / (2.0 * _math.sin(_math.pi / sides))
    first = FreeCAD.Vector(R * _math.cos(rot), R * _math.sin(rot), 0.0)

    RegularPolygon = _load_profile_lib()
    RegularPolygon.makeRegularPolygon(sk, sides, FreeCAD.Vector(0, 0, 0), first)
    sk.Document.recompute()

    nc = len(sk.Geometry) - 1  # construction circle is the last geometry
    sk.addConstraint(Constraint("Radius", nc, R))
    sk.Document.recompute()
    sk.addConstraint(Constraint("DistanceX", nc, 3, 0.0))
    sk.Document.recompute()
    sk.addConstraint(Constraint("DistanceY", nc, 3, 0.0))
    sk.Document.recompute()
    # the first corner is already pinned onto the construction circle (the
    # PointOnObject added by ProfileLib), so a single horizontal distance
    # fixes the rotation; a second vertical distance would be redundant.
    sk.addConstraint(Constraint("DistanceX", 0, 1, R * _math.cos(rot)))
    sk.Document.recompute()

    # let FreeCAD's solver drop any constraint it considers redundant
    try:
        sk.autoRemoveRedundants()
        sk.Document.recompute()
    except Exception:
        pass


def _inner_dimension(ptype, dim, wall):
    """Dimension of the inner cross-section for a wall of thickness *wall*."""
    if wall <= 0:
        return 0.0
    if ptype == "Circle":
        return dim - wall
    sides = _POLY_SIDES.get(ptype)
    if sides is None:
        return 0.0
    apothem = dim / (2.0 * math.tan(math.pi / sides))
    inner_apothem = apothem - wall
    if inner_apothem <= 0:
        return 0.0
    return 2.0 * inner_apothem * math.tan(math.pi / sides)


def _create_native_pipe(doc, body, wire, profile_type, dimension, rotation_deg, offset, corner_name, wall_thickness, subtractive, spine_refs=None, wire_frame=None):
    """Create a native PartDesign pipe on a body.

    The profile is drawn 'perpendicular to the path': a datum plane is placed
    at the path start with its normal along the first tangent, and the fully
    constrained profile sketch lives on that plane. The native AdditivePipe /
    SubtractivePipe receives the profile directly as the sketch reference
    (Profile = (sketch, [])); the spine is the path the user pre-selected when
    starting the command (*spine_refs*, a list of (object, [edge names])),
    passed unchanged to the native pipe (a bare (object, [names]) when a
    single object owns all selected edges). No carrier object is created.

    *wire_frame* is the document placement of the frame in which *wire* is
    expressed: a placement when the path comes from another PartDesign body
    (its shape is body-local), or None when the wire is already in global
    coordinates. It is used to bring the datum plane (a child of *body*, hence
    in body-local coordinates) onto the real path start.

    Returns the last operation (the feature that should become the Tip).
    """
    tan = _path_tangent(wire)
    if tan is None:
        raise ValueError(_tr("Could not determine the direction of the path"))
    base = wire.OrderedEdges[0].Vertexes[0].Point + (offset or FreeCAD.Vector(0, 0, 0))

    # profile frame exactly as the preview computes it (in the wire's frame)
    n1, n2 = _build_frame(tan)

    # The wire may live in the target body's frame, in another body's frame or
    # in global coordinates; the datum plane is always a child of *body*, so
    # express base/tangent/frame in body-local coordinates before placing it.
    if body is not None:
        try:
            conv = body.getGlobalPlacement().inverse().multiply(
                wire_frame if wire_frame is not None else FreeCAD.Placement())
            base = conv.multVec(base)
            tan = conv.Rotation.multVec(tan)
            n1 = conv.Rotation.multVec(n1)
            n2 = conv.Rotation.multVec(n2)
        except Exception:
            pass

    created = []

    def _rollback():
        # keep the datum plane and the profile sketches (hidden) so the user
        # can inspect them after a failure; only remove the broken pipe
        # operation(s) that were already created
        for n in created:
            try:
                obj = doc.getObject(n)
                if obj is None:
                    continue
                if "AdditivePipe" in obj.TypeId or "SubtractivePipe" in obj.TypeId:
                    doc.removeObject(n)
                    continue
                if obj.ViewObject is not None:
                    obj.ViewObject.Visibility = False
            except Exception:
                pass

    try:
        # 1) datum plane perpendicular to the path
        plane = doc.addObject("PartDesign::Plane", "PipePlane")
        created.append(plane.Name)
        body.addObject(plane)
        plane.MapMode = "Deactivated"
        plane.Placement = FreeCAD.Placement(base, _frame_rotation(n1, n2, tan))
        doc.recompute()

        def _profile_sketch(name):
            sk = doc.addObject("Sketcher::SketchObject", name)
            created.append(sk.Name)
            body.addObject(sk)
            sk.AttachmentSupport = [(plane, "")]
            sk.MapMode = "FlatFace"
            doc.recompute()
            return sk

        # 2) fully constrained profile sketch on the plane
        sk = _profile_sketch("PipeProfile")
        _build_fc_profile(sk, profile_type, dimension, rotation_deg)

        # 3) spine: the pre-selected path edges, unchanged. A single object is
        #    a bare (object, [edge names]) reference (the user-proven form);
        #    several objects become a list of such pairs. A sketch used whole
        #    as path is a bare (sketch, []) reference. No extra carrier object
        #    is needed either way.
        if not spine_refs:
            raise ValueError(
                _tr("No path was given to the pipe: select a sketch or edges."))
        if len(spine_refs) == 1:
            spine = (spine_refs[0][0], list(spine_refs[0][1]))
        else:
            spine = [(o, list(n)) for o, n in spine_refs if o is not None and n]

        # the fully constrained profile sketch IS the pipe profile
        prof = (sk, [])

        _TRANSITION_FALLBACKS = ("Right corner", "Round corner")

        def _pipe_feature(feature_type, fname, prof_ref, policy="add"):
            op = doc.addObject(feature_type, fname)
            created.append(op.Name)
            body.addObject(op)
            op.Profile = prof_ref
            op.Spine = spine
            op.Transition = corner_name
            doc.recompute()
            # 'Transformed' re-orients the cross-section instantly at a sharp
            # path kink and can self-intersect, yielding an invalid/null
            # shape; retry with a kink-safe transition (mirrors the retry
            # already done by build_pipe_from_wire for the live preview).
            shp = getattr(op, "Shape", None)
            if (shp is None or shp.isNull() or not shp.isValid()) and corner_name not in _TRANSITION_FALLBACKS:
                for alt in _TRANSITION_FALLBACKS:
                    op.Transition = alt
                    doc.recompute()
                    shp = getattr(op, "Shape", None)
                    if shp is not None and not shp.isNull() and shp.isValid():
                        FreeCAD.Console.PrintWarning(
                            _tr("Corner transition '{}' not possible on this path: "
                                "using '{}'.").format(corner_name, alt) + "\n")
                        break
            if shp is None or shp.isNull() or not shp.isValid():
                raise ValueError(
                    _tr("The native pipe could not be built on this path "
                        "(fatal error). Use a single chain of connected edges, "
                        "or change the corner transition or profile size."))
            return op

        def _hide(obj):
            # helper operands (datum plane, profile sketches, wire carriers)
            # must not stay visible: only the pipe feature/body remains shown
            try:
                if obj is not None and obj.ViewObject is not None:
                    obj.ViewObject.Visibility = False
            except Exception:
                pass

        # solid tool (covers both additive and subtractive modes)
        tool = _pipe_feature(
            "PartDesign::SubtractivePipe" if subtractive else "PartDesign::AdditivePipe",
            "PipeCut" if subtractive else "Pipe",
            prof,
        )
        _hide(plane)
        _hide(sk)
        if wall_thickness <= 0 or subtractive:
            return tool

        # 4) hollowness: additive outer pipe + subtractive inner pipe
        inner_dim = _inner_dimension(profile_type, dimension, wall_thickness)
        if inner_dim <= 0:
            FreeCAD.Console.PrintWarning(
                _tr("Wall thickness too large for the profile: keeping a solid pipe.") + "\n")
            return tool
        sk_in = _profile_sketch("PipeProfileInner")
        _build_fc_profile(sk_in, profile_type, inner_dim, rotation_deg)
        _hide(sk_in)
        cut = _pipe_feature("PartDesign::SubtractivePipe", "PipeCut", (sk_in, []))
        return cut
    except Exception:
        _rollback()
        raise


# =============================================================================
# Pipe features
# =============================================================================

def _get_shape_element(obj, name):
    """Extract a named sub-element (e.g. 'Edge2') from an object's shape."""
    try:
        return obj.Shape.getElement(name)
    except (AttributeError, Part.OCCError):
        pass
    try:
        return obj.Shape.getSubObject(name)
    except Exception:
        return None


def _path_wire_from_pipe(fp):
    """Build the path wire of a pipe feature from its PathSketch or PathEdges."""
    sk = getattr(fp, "PathSketch", None)
    if sk is not None:
        edges = sk.Shape.Edges
        if not edges:
            raise ValueError("The referenced sketch/path is empty")
        return Part.Wire(edges)
    subs = getattr(fp, "PathEdges", None)
    if subs:
        edges = []
        for parts in subs:
            obj, names = parts[0], parts[1]
            for name in names:
                s = _get_shape_element(obj, name)
                if s is not None:
                    edges.append(s)
        if not edges:
            raise ValueError("No edges selected as path")
        return Part.Wire(edges)
    return None


def _setup_pipe_properties(obj):
    if not hasattr(obj, "PathSketch"):
        obj.addProperty("App::PropertyLink", "PathSketch", "Pipe")
    if not hasattr(obj, "PathEdges"):
        obj.addProperty("App::PropertyLinkSubList", "PathEdges", "Pipe")
    if not hasattr(obj, "ProfileType"):
        obj.addProperty(
            "App::PropertyEnumeration",
            "ProfileType",
            "Pipe",
        )
        obj.ProfileType = ["Circle", "Square", "Triangle", "Pentagon", "Hexagon", "Octagon"]
    if not hasattr(obj, "ProfileDimension"):
        obj.addProperty(
            "App::PropertyLength",
            "ProfileDimension",
            "Pipe",
        )
        obj.ProfileDimension = 5
    if not hasattr(obj, "ProfileRotation"):
        obj.addProperty(
            "App::PropertyFloat",
            "ProfileRotation",
            "Pipe",
        )
        obj.ProfileRotation = 0.0
    if not hasattr(obj, "ProfileOffset"):
        obj.addProperty(
            "App::PropertyVector",
            "ProfileOffset",
            "Pipe",
        )
        obj.ProfileOffset = FreeCAD.Vector(0, 0, 0)
    if not hasattr(obj, "WallThickness"):
        obj.addProperty(
            "App::PropertyLength",
            "WallThickness",
            "Pipe",
        )
        obj.WallThickness = 0.0
    if not hasattr(obj, "CornerMode"):
        obj.addProperty(
            "App::PropertyEnumeration",
            "CornerMode",
            "Pipe",
        )
        obj.CornerMode = ["Right corner", "Round corner", "Transformed"]
    if not hasattr(obj, "Refine"):
        obj.addProperty(
            "App::PropertyBool",
            "Refine",
            "Pipe",
        )
        obj.Refine = True


def _refine(shape):
    """Return a refined (splitter-free) copy of *shape*."""
    if shape is None or shape.isNull() or not shape.isValid():
        return shape
    try:
        return shape.removeSplitter()
    except Exception:
        return shape


class PipeFeature:
    """Standalone parametric pipe that sweeps a profile along a path."""

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "PipeFeature"
        _setup_pipe_properties(obj)

    def execute(self, fp):
        try:
            wire = _path_wire_from_pipe(fp)
            if wire is None:
                fp.Shape = Part.Shape()
                return
            shape = build_pipe_from_wire(wire, fp.ProfileType, float(fp.ProfileDimension), math.radians(fp.ProfileRotation), fp.ProfileOffset, _CORNER_MODES.get(fp.CornerMode, 1), fp.WallThickness)
            fp.Shape = _refine(shape) if fp.Refine else shape
        except Exception as e:
            FreeCAD.Console.PrintError("PipeFeature.execute error: {}\n".format(e))
            fp.Shape = Part.Shape()


class AdditivePipeFeature:
    """PartDesign additive pipe: swept profile fused with the body tip."""

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "AdditivePipeFeature"
        _setup_pipe_properties(obj)

    def execute(self, fp):
        try:
            wire = _path_wire_from_pipe(fp)
            if wire is None:
                fp.Shape = Part.Shape()
                return
            raw = build_pipe_from_wire(wire, fp.ProfileType, float(fp.ProfileDimension), math.radians(fp.ProfileRotation), fp.ProfileOffset, _CORNER_MODES.get(fp.CornerMode, 1), fp.WallThickness)
            base = getattr(fp, "BaseFeature", None)
            if base is not None and base.Shape is not None and not base.Shape.isNull():
                shape = base.Shape.fuse(raw)
            else:
                shape = raw
            fp.Shape = _refine(shape) if fp.Refine else shape
        except Exception as e:
            FreeCAD.Console.PrintError("AdditivePipeFeature.execute error: {}\n".format(e))
            fp.Shape = Part.Shape()


class SubtractivePipeFeature:
    """PartDesign subtractive pipe: swept profile removed from the body tip."""

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "SubtractivePipeFeature"
        _setup_pipe_properties(obj)

    def execute(self, fp):
        try:
            wire = _path_wire_from_pipe(fp)
            if wire is None:
                fp.Shape = Part.Shape()
                return
            raw = build_pipe_from_wire(wire, fp.ProfileType, float(fp.ProfileDimension), math.radians(fp.ProfileRotation), fp.ProfileOffset, _CORNER_MODES.get(fp.CornerMode, 1), fp.WallThickness)
            base = getattr(fp, "BaseFeature", None)
            if base is not None and base.Shape is not None and not base.Shape.isNull():
                shape = base.Shape.cut(raw)
            else:
                FreeCAD.Console.PrintError(
                    "SubtractivePipeFeature needs an existing body to subtract from.\n")
                shape = Part.Shape()
            fp.Shape = _refine(shape) if fp.Refine else shape
        except Exception as e:
            FreeCAD.Console.PrintError("SubtractivePipeFeature.execute error: {}\n".format(e))
            fp.Shape = Part.Shape()


# =============================================================================
# Selection helpers
# =============================================================================

def _drop_concentric_circles(edge_refs):
    """Remove accidental duplicate circular borders from one object's selection."""
    out = []
    for obj, names in edge_refs:
        circ_idx = []
        rest = []
        for i, name in enumerate(names):
            s = _get_shape_element(obj, name)
            curve = getattr(s, "Curve", None)
            if curve is not None and curve.__class__.__name__ == "Circle":
                circ_idx.append(i)
            else:
                rest.append(i)
        if len(circ_idx) <= 1:
            out.append((obj, names))
            continue
        info = []
        non_full = []
        for i in circ_idx:
            s = _get_shape_element(obj, names[i])
            c = s.Curve
            perimeter = 2 * math.pi * c.Radius
            if abs(s.Length - perimeter) > 1e-3 * perimeter:
                non_full.append(i)
            else:
                info.append((c.Radius, i))
        keep = non_full
        if info:
            keep.append(max(info)[1])
        kept_names = [names[i] for i in sorted(set(keep))]
        out.append((obj, kept_names))
    return out


def _collect_path_from_selection():
    """Return (sketch_or_None, [(obj, [subnames...]), ...], body_or_None)."""
    import FreeCADGui as Gui

    sketch = None
    edge_refs = []
    target_body = None
    for se in Gui.Selection.getSelectionEx():
        obj = se.Object
        if obj is None:
            continue
        if obj.TypeId == "PartDesign::Body":
            if target_body is None:
                target_body = obj
            continue
        if "Sketch" in obj.TypeId:
            if sketch is None:
                sketch = obj
            continue
        subs = []
        for name in se.SubElementNames:
            if name.startswith("Edge"):
                subs.append(name)
        if subs:
            edge_refs.append((obj, subs))
    return sketch, edge_refs, target_body


def _parent_body(obj, doc):
    """Return the PartDesign body owning obj (via Group membership), if any."""
    try:
        for b in doc.Objects:
            if b.TypeId != "PartDesign::Body":
                continue
            if obj in (list(getattr(b, "Group", [])) or []):
                return b
            for f in (list(getattr(b, "Group", [])) or []):
                if f is not obj and obj in (getattr(f, "InList", []) or []):
                    return b
    except Exception:
        pass
    return None


def _set_view_object_ok(obj):
    """Set a minimal view provider without crashing in console mode."""
    try:
        import FreeCADGui as Gui
    except Exception:
        return

    vobj = getattr(obj, "ViewObject", None)
    if vobj is None or not hasattr(vobj, "Proxy"):
        return
    try:
        from . import ViewProvider

        ViewProvider.FormsViewProvider(vobj)
    except Exception:
        import traceback

        traceback.print_exc()


def _copy_appearance(src_vobj, dst_vobj):
    """Copy the color look (material/diffuse/transparency) to a new feature.

    FreeCAD's PartDesign body only propagates visual properties to features
    that already exist when the body's appearance changes, not to features
    added later. A freshly created pipe feature would otherwise become the
    Tip with the default gray material and 'un-color' the body.
    """
    if src_vobj is None or dst_vobj is None:
        return
    for prop in ("ShapeAppearance", "DiffuseColor", "Transparency"):
        if not hasattr(src_vobj, prop) or not hasattr(dst_vobj, prop):
            continue
        try:
            value = getattr(src_vobj, prop)
            setattr(dst_vobj, prop, value)
        except Exception:
            pass


# =============================================================================
# Public command
# =============================================================================

def create_pipe(subtractive=False):
    """Create a pipe from a sketch or from edges of an existing body/object.

    The profile is chosen in a small dialog. In additive mode (default) the
    pipe is fused into the body (or created standalone). In subtractive mode
    the swept profile is removed from the body.
    """
    import FreeCADGui as Gui

    doc = FreeCAD.ActiveDocument
    if doc is None:
        FreeCAD.Console.PrintError(_tr("No active document") + "\n")
        return

    sketch, edge_refs, sel_body = _collect_path_from_selection()
    edge_refs = _drop_concentric_circles(edge_refs)
    if sketch is None and not edge_refs:
        FreeCAD.Console.PrintMessage(
            _tr("Select a sketch, or one or more edges of a body, as the pipe path.") + "\n")
        return
    if sketch is not None and not sketch.Shape.Edges:
        FreeCAD.Console.PrintError(_tr("The selected sketch is empty.") + "\n")
        return

    # quick validation that a path wire can be built from the selection
    try:
        if sketch is not None:
            Part.Wire(sketch.Shape.Edges)
        else:
            edges = []
            for obj, names in edge_refs:
                for name in names:
                    s = _get_shape_element(obj, name)
                    if s is not None:
                        edges.append(s)
            Part.Wire(edges)
    except Exception as e:
        FreeCAD.Console.PrintError(
            _tr("The selected edges do not form a connected path: {}").format(e) + "\n")
        return

    # find the target body: selected body, body of sketch, body of edge owner, active body
    body = sel_body
    if body is None and sketch is not None:
        body = _parent_body(sketch, doc)
    if body is None and edge_refs:
        body = _parent_body(edge_refs[0][0], doc)
    if body is None:
        try:
            body = Gui.activeView().getActiveObject("pdbody")
        except Exception:
            body = None
    if body is None:
        # only one body in the document: use it (common PartDesign flow)
        bodies = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
        if len(bodies) == 1:
            body = bodies[0]

    # path reference(s) and the frame the path wire is expressed in. A path
    # drawn in another PartDesign body has body-local coordinates, a standalone
    # sketch/shape has global coordinates; both must be brought into the target
    # body's frame before the datum plane (a body child) is placed on them.
    if edge_refs:
        path_refs = edge_refs
    elif sketch is not None:
        path_refs = [(sketch, [])]
    else:
        path_refs = None
    _src = sketch if sketch is not None else (edge_refs[0][0] if edge_refs else None)
    _src_body = _parent_body(_src, doc) if _src is not None else None
    wire_frame = _src_body.getGlobalPlacement() if _src_body is not None else None

    def _to_global(shape, frame):
        if shape is None or frame is None:
            return shape
        try:
            sh = shape.copy()
            sh.transformShape(frame.toMatrix())
            return sh
        except Exception:
            return shape

    from .PipeDialog import PipeProfilePanel

    def _build_wire():
        if sketch is not None:
            return Part.Wire(sketch.Shape.Edges)
        edges = []
        for obj, names in edge_refs:
            for name in names:
                s = _get_shape_element(obj, name)
                if s is not None:
                    edges.append(s)
        return Part.Wire(edges)

    def _shape_of(ptype, dim, rot_deg, off_xy, corner, thick, mode="tool"):
        try:
            wire = _build_wire()
            tan = _path_tangent(wire)
            offset = _offset_from_dialog(tan, off_xy[0], off_xy[1])
            raw = build_pipe_from_wire(wire, ptype, dim, math.radians(rot_deg), offset,
                                       _CORNER_MODES.get(corner, 1), thick)
            raw = _to_global(raw, wire_frame)
            if mode != "tool" and body is not None:
                tip = getattr(body, "Tip", None)
                if tip is not None and tip.Shape is not None and not tip.Shape.isNull():
                    try:
                        tip_shape = _to_global(tip.Shape, body.getGlobalPlacement())
                        if subtractive:
                            raw = tip_shape.cut(raw)
                        else:
                            raw = tip_shape.fuse(raw)
                    except Exception:
                        pass
            return _refine(raw)
        except Exception:
            return None

    hidden_tip = {"obj": None, "was": True}

    def _hide_body_for_preview():
        """Hide the body solid so only the preview shape is visible."""
        if body is None:
            return
        tip = getattr(body, "Tip", None)
        if tip is None:
            return
        try:
            nano = str(tip.Name)
        except Exception:
            return
        # remember which tip we hid and restore its previous visibility on close
        if hidden_tip["obj"] is not None:
            return  # already hidden
        hidden_tip["obj"] = nano
        try:
            hidden_tip["was"] = bool(tip.ViewObject.Visibility)
        except Exception:
            hidden_tip["was"] = True
        try:
            tip.ViewObject.Visibility = False
        except Exception:
            pass

    def _restore_body_visibility(restore=True):
        if hidden_tip["obj"] is None:
            return
        tip = doc.getObject(hidden_tip["obj"])
        hidden_tip["obj"] = None
        if tip is None:
            return
        if not restore:
            return
        try:
            tip.ViewObject.Visibility = hidden_tip["was"]
        except Exception:
            pass

    def _remove_preview(restore=True):
        pv = doc.getObject("PipePreview")
        if pv is not None:
            try:
                doc.removeObject(pv.Name)
            except Exception:
                pass
        _restore_body_visibility(restore)

    def _on_change(ptype, dim, rot_deg, off_xy, corner, thick, mode="tool"):
        shp = _shape_of(ptype, dim, rot_deg, off_xy, corner, thick, mode)
        pv = doc.getObject("PipePreview")
        if shp is None:
            _remove_preview()
            return
        if pv is None:
            pv = doc.addObject("Part::Feature", "PipePreview")
            _set_view_object_ok(pv)
            try:
                pv.ViewObject.Selectable = False
            except Exception:
                pass
        if mode == "result":
            # final result replaces the body: hide the body so only the
            # result shape is visible
            _hide_body_for_preview()
        else:
            # overlap mode: keep the body visible to see the profile on it
            _restore_body_visibility()
        try:
            if mode == "result":
                # show the real result of the boolean, like the body itself
                pv.ViewObject.ShapeColor = (0.7, 0.7, 0.7, 1.0)
                pv.ViewObject.Transparency = 0
            elif subtractive:
                # violet tool volume to be removed (native subtractive color)
                pv.ViewObject.ShapeColor = (0.62, 0.40, 0.80, 1.0)
                pv.ViewObject.Transparency = 40
            else:
                # green tool volume being added (native additive color)
                pv.ViewObject.ShapeColor = (0.0, 0.70, 0.0, 1.0)
                pv.ViewObject.Transparency = 40
        except Exception:
            pass
        pv.Shape = shp
        pv.Visibility = True
        try:
            doc.recompute()
        except Exception:
            pass

    def _on_finish(ptype, dim, rot_deg, off_xy, corner, thick, mode="tool"):
        newfeat = None
        try:
            wire = _build_wire()
            offset = _offset_from_dialog(_path_tangent(wire), off_xy[0], off_xy[1])
            if body is not None:
                # ---- native PartDesign pipe ----
                old_tip = getattr(body, "Tip", None)
                newfeat = _create_native_pipe(
                    doc, body, wire, ptype, dim, rot_deg,
                    offset, corner, thick, subtractive,
                    spine_refs=path_refs, wire_frame=wire_frame)
                doc.recompute()
                try:
                    body.Tip = newfeat
                except Exception:
                    pass
                doc.recompute()
                try:
                    if old_tip is not None and old_tip.ViewObject is not None:
                        _copy_appearance(old_tip.ViewObject, newfeat.ViewObject)
                except Exception:
                    pass
                if subtractive:
                    FreeCAD.Console.PrintMessage(
                        _tr("Subtractive pipe removed from '{}'.").format(body.Label) + "\n")
                else:
                    FreeCAD.Console.PrintMessage(
                        _tr("Additive pipe added to '{}'.").format(body.Label) + "\n")
            else:
                # ---- standalone pipe (no body): legacy FeaturePython ----
                if subtractive:
                    FreeCAD.Console.PrintError(
                        _tr("Subtractive pipe needs a PartDesign body to cut.") + "\n")
                    return
                obj = doc.addObject("Part::FeaturePython", "FormsPipe")
                PipeFeature(obj)
                if sketch is not None:
                    obj.PathSketch = sketch
                else:
                    obj.PathEdges = edge_refs
                obj.ProfileType = ptype
                obj.ProfileDimension = dim
                obj.ProfileRotation = rot_deg
                obj.ProfileOffset = offset
                obj.CornerMode = corner
                obj.WallThickness = thick
                _set_view_object_ok(obj)
                newfeat = obj
                doc.recompute()
                FreeCAD.Console.PrintMessage(_tr("Pipe created.") + "\n")
        finally:
            # do not bring back the old tip: the new feature must be shown
            _remove_preview(restore=False)
            try:
                import FreeCADGui as Gui
                Gui.Selection.clearSelection()
                if newfeat is not None and newfeat.ViewObject is not None:
                    newfeat.ViewObject.Visibility = True
            except Exception:
                pass

    def _on_cancel():
        _remove_preview()

    # open the non-modal task panel; create_pipe returns immediately and the
    # 3D view keeps working while the user tweaks the values and inspects
    # the live preview.
    try:
        if Gui.Control.activeDialog():
            Gui.Control.closeDialog()
    except Exception:
        pass
    Gui.Control.showDialog(PipeProfilePanel(_on_change, _on_finish, _on_cancel))