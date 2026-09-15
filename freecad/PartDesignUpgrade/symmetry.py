# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Symmetry (Mirror) helper for PartDesignUpgrade.

Run the "Mirror (Symmetry)" command on a PartDesign body: a dialog lets the
user pick a reference (plane, axis or point) that starts at the centre of the
body and can be moved with the three fundamental-plane buttons plus an offset.
Pressing OK mirrors the solid:

- plane  -> parametric PartDesign::Mirrored,
- axis   -> parametric PartDesign::PolarPattern (180 deg, 2 occurrences),
- point  -> a static Part::Feature copy reflected through the point.
"""

import FreeCAD
import Part

from .translations import tr as _tr

_PROP_GROUP = "Symmetry"
_REF_NAME = "SymmetryRef"
_TRANSFORM_NAME = "SymmetryTransform"

# last choice recorded by the task panel, reused when re-enabling from the
# floating window: {"kind": "plane"/"axis"/"point", "target": ..., "offset": ...}
_last_choice = None

# name of the reference datum the panel is currently working on. New mirror
# operations use this plane; already-built symmetries keep their own datum,
# which is left untouched (never repointed, never deleted).
_active_ref_name = None

# (reference type, target) -> (datum TypeId, centering vector, normal)
_AXIS_ROTATIONS = {
    "X": lambda: FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90),
    "Y": lambda: FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -90),
    "Z": lambda: FreeCAD.Rotation(),
}
# axis movements: the two directions perpendicular to the axis, as
# [(label, vector), (label, vector)]
_AXIS_MOVES = {
    "X": (("Y", (0, 1, 0)), ("Z", (0, 0, 1))),
    "Y": (("X", (1, 0, 0)), ("Z", (0, 0, 1))),
    "Z": (("X", (1, 0, 0)), ("Y", (0, 1, 0))),
}
_POINT_MOVES = (("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1)))
_AXIS_LATERAL = {
    "X": FreeCAD.Vector(0, 1, 0),
    "Y": FreeCAD.Vector(1, 0, 0),
    "Z": FreeCAD.Vector(1, 0, 0),
}


def _msg(text, error=False):
    if error:
        FreeCAD.Console.PrintError(text + "\n")
    else:
        FreeCAD.Console.PrintMessage(text + "\n")


_DATUM_TYPES = ("Part::DatumPlane", "Part::DatumLine", "Part::DatumPoint",
                "PartDesign::Plane", "PartDesign::Line", "PartDesign::Point",
                "PartDesign::CoordinateSystem")


def _is_transform_feature(feat):
    return feat is not None and feat.TypeId.startswith("PartDesign::") \
        and feat.TypeId not in _DATUM_TYPES


def _active_body(doc):
    try:
        import FreeCADGui as Gui
        b = Gui.activeBody()
        if b is not None:
            return b
    except Exception:
        pass
    try:
        import FreeCADGui as Gui
        for o in Gui.Selection.getSelection():
            if o is not None and o.TypeId == "PartDesign::Body":
                return o
    except Exception:
        pass
    body = None
    for o in doc.Objects:
        if o.TypeId == "PartDesign::Body":
            if body is None:
                body = o
            else:
                body = None
                break
    return body


def reset(body, doc):
    """Remove any leftover symmetry reference and transform objects.

    The mirror is only removed when nothing else in the body depends on it.
    If later features (a sketch mapped on the mirrored face, a pocket, ...)
    reference the transform, it is kept so the body is not destroyed.
    Returns True when removed (or there was nothing to remove), False when
    the mirror had to be kept because it is used by other features.
    """
    transform = doc.getObject(_TRANSFORM_NAME)
    if transform is not None and body.Tip is not transform:
        for feat in (getattr(body, "Group", []) or []):
            if feat is None or feat is transform:
                continue
            try:
                depends = transform in (feat.InList or [])
            except Exception:
                depends = False
            if depends:
                _msg(_tr(
                    "The mirror is kept because the features that follow "
                    "depend on it: removing it would break the body."))
                return False
    if transform is not None and body.Tip is transform:
        prev = None
        for f in (getattr(body, "Group", []) or []):
            if f is transform or not _is_transform_feature(f):
                continue
            prev = f
        if prev is not None:
            try:
                body.Tip = prev
            except Exception:
                pass
    for o in list(doc.Objects):
        if o is None:
            continue
        n = o.Name
        if n == _TRANSFORM_NAME or n == _REF_NAME \
                or n.startswith(_TRANSFORM_NAME) or n.startswith(_REF_NAME):
            try:
                body.removeObject(n)
            except Exception:
                try:
                    doc.removeObject(n)
                except Exception:
                    pass
    try:
        doc.recompute()
    except Exception:
        pass
    return True


def _is_seq(v):
    return isinstance(v, (tuple, list))


def _datum_extents(bbox, rot, length_only=False):
    """Projection of the bounding box onto the datum axes, kept a bit larger
    than the body so the reference is easy to see. Returns (length, width) for
    a plane or just the length for a line. FreeCAD ignores null boxes."""
    try:
        if bbox is None or bbox.XLength <= 0 or bbox.YLength <= 0:
            raise ValueError("null bounding box")
    except Exception:
        return (20.0, 20.0) if not length_only else 30.0
    half = (bbox.XLength / 2.0, bbox.YLength / 2.0, bbox.ZLength / 2.0)

    def proj(axis):
        return 2.0 * (abs(axis.x) * half[0]
                      + abs(axis.y) * half[1]
                      + abs(axis.z) * half[2])

    margin = 1.25
    if length_only:
        length = proj(rot.multVec(FreeCAD.Vector(0, 0, 1)))
        return max(length * margin, 5.0)
    length = proj(rot.multVec(FreeCAD.Vector(1, 0, 0)))
    width = proj(rot.multVec(FreeCAD.Vector(0, 1, 0)))
    return (max(length * margin, 5.0), max(width * margin, 5.0))


def create_reference(body, ref_type, target, center, offset=0.0):
    """Create the symmetry reference datum inside the body.

    ref_type: 'plane', 'axis' or 'point'.
    target:   'XY'/'XZ'/'YZ' for planes, 'X'/'Y'/'Z' for axes, '' for points.
    center:   FreeCAD.Vector, centre of the body bounding box.
    offset:   mm, moves the reference away from the centre. For a plane it is
              a single value along the plane normal. For an axis it is a
              scalar (legacy, first lateral direction) or a 2-tuple for the
              two independent perpendicular movements. For a point it is a
              3-tuple (dx, dy, dz).
    """
    try:
        bbox = body.Shape.BoundBox if body is not None else None
        if ref_type == "plane":
            d = body.newObject("PartDesign::Plane", _REF_NAME)
            d.MapMode = "Deactivated"
            if target == "XY":
                base = FreeCAD.Vector(center.x, center.y, center.z + offset)
                rot = FreeCAD.Rotation()
            elif target == "XZ":
                base = FreeCAD.Vector(center.x, center.y + offset, center.z)
                rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -90)
            else:  # YZ
                base = FreeCAD.Vector(center.x + offset, center.y, center.z)
                rot = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90)
            d.Placement = FreeCAD.Placement(base, rot)
            d.ResizeMode = "Manual"
            length, width = _datum_extents(bbox, rot)
            d.Length = length
            d.Width = width
        elif ref_type == "axis":
            d = body.newObject("PartDesign::Line", _REF_NAME)
            d.MapMode = "Deactivated"
            try:
                d1 = float(offset[0])
                d2 = float(offset[1])
            except Exception:
                d1 = float(offset)
                d2 = 0.0
            moves = _AXIS_MOVES[target]
            base = center + FreeCAD.Vector(*moves[0][1]) * d1 \
                + FreeCAD.Vector(*moves[1][1]) * d2
            rot = _AXIS_ROTATIONS[target]()
            d.Placement = FreeCAD.Placement(base, rot)
            d.ResizeMode = "Manual"
            d.Length = _datum_extents(bbox, rot, length_only=True)
        else:
            d = body.newObject("PartDesign::Point", _REF_NAME)
            d.MapMode = "Deactivated"
            try:
                dx, dy, dz = (float(offset[0]), float(offset[1]),
                              float(offset[2]))
            except Exception:
                try:
                    dx, dy, dz = (float(offset[0]), float(offset[1]), 0.0)
                except Exception:
                    dx, dy, dz = 0.0, 0.0, float(offset)
            d.Placement = FreeCAD.Placement(
                center + FreeCAD.Vector(dx, dy, dz), FreeCAD.Rotation())
        _mark_active_reference(d)
        return d
    except Exception as exc:
        _msg(_tr("Could not create the symmetry reference: {}").format(exc),
             error=True)
        return None


def _mark_active_reference(ref):
    """Remember the datum the panel currently works on, so new mirror
    operations use it while previously built symmetries keep their own."""
    global _active_ref_name
    if ref is None:
        return
    _active_ref_name = ref.Name


def set_mirror(doc, body, on):
    """Enable or disable the native mirror without needing the task panel.

    When turning on, the last choice recorded by the task panel is reused (or
    a default reference). Returns True when the desired state is reached."""
    try:
        if on:
            reset(body, doc)
            c = body.Shape.BoundBox.Center
            ch = _last_choice or {}
            kind = ch.get("kind", "plane")
            target = ch.get("target", "XY")
            offset = ch.get("offset", 0.0)
            ref = create_reference(body, kind, target, c, offset)
            if ref is None:
                return False
            return mirror_solid(body, doc, ref)
        reset(body, doc)
        try:
            doc.recompute()
        except Exception:
            pass
        return True
    except Exception as exc:
        _msg(_tr("Could not apply the symmetry: {}").format(exc), error=True)
        return False


def mirror_solid(body, doc, ref):
    """Mirror the whole body around the given reference datum."""
    if ref is None:
        return False
    features = [f for f in (getattr(body, "Group", []) or [])
                if _is_transform_feature(f)]
    if not features:
        _msg(_tr("No PartDesign features to mirror."), error=True)
        return False
    try:
        if ref.TypeId in ("Part::DatumPlane", "PartDesign::Plane"):
            return _mirror_about_plane(body, doc, ref, features)
        if ref.TypeId in ("Part::DatumLine", "PartDesign::Line"):
            return _pattern_about_axis(body, doc, ref, features)
        if ref.TypeId in ("Part::DatumPoint", "PartDesign::Point"):
            return _point_symmetry(body, doc, ref)
        _msg(_tr("Unsupported symmetry reference: {}").format(ref.TypeId),
             error=True)
        return False
    except Exception as exc:
        _msg(_tr("Mirror failed: {}").format(exc), error=True)
        return False


def _mirror_about_plane(body, doc, ref, features, originals=None):
    tip = body.Tip
    if not _is_transform_feature(tip):
        tip = features[-1] if features else None
    if tip is None:
        _msg(_tr("No PartDesign feature to mirror."), error=True)
        return False
    try:
        s = tip.Shape
        if s is None or s.isNull() or not s.isValid() \
                or not s.Solids:
            _msg(_tr(
                "The last operation has an invalid shape (no solid to "
                "mirror): check the feature it depends on."),
                error=True)
            return False
    except Exception:
        _msg(_tr(
            "The last operation has an invalid shape: check the feature "
            "it depends on."), error=True)
        return False
    t = body.newObject("PartDesign::Mirrored", _TRANSFORM_NAME)
    t.addProperty("App::PropertyBool", "SymmetryTransform", _PROP_GROUP, "")
    t.SymmetryTransform = True
    t.TransformMode = "Features"
    t.Originals = originals if originals is not None else [tip]
    t.MirrorPlane = (ref, "Original")
    try:
        body.Tip = t
    except Exception:
        pass
    doc.recompute()
    t.Label = _tr("Mirror (symmetry)")
    try:
        st = t.Shape
        valid = st is not None and not st.isNull() and st.isValid() and st.Solids
    except Exception:
        valid = False
    if not valid:
        _msg(_tr("Mirror failed: the mirrored shape is invalid."), error=True)
        return False
    try:
        ob = tip.Shape.BoundBox
        mb = st.BoundBox
        overlap = (abs(ob.XLength - mb.XLength) < 1e-6
                   and abs(ob.YLength - mb.YLength) < 1e-6
                   and abs(ob.ZLength - mb.ZLength) < 1e-6
                   and abs(ob.XMin - mb.XMin) < 1e-4
                   and abs(ob.YMin - mb.YMin) < 1e-4
                   and abs(ob.ZMin - mb.ZMin) < 1e-4)
    except Exception:
        overlap = False
    if overlap:
        _msg(_tr("Mirrored the last operation around the symmetry plane. "
                 "The copy overlaps the original exactly (the plane passes "
                 "through the symmetry plane of the body)."))
    else:
        _msg(_tr("Mirrored the last operation around the symmetry plane."))
    return True


def _pattern_about_axis(body, doc, ref, features, originals=None):
    sel = originals if originals is not None else features
    t = body.newObject("PartDesign::PolarPattern", _TRANSFORM_NAME)
    t.addProperty("App::PropertyBool", "SymmetryTransform", _PROP_GROUP, "")
    t.SymmetryTransform = True
    t.Originals = sel
    t.Axis = (ref, "Original")
    t.Angle = 180
    t.Occurrences = 2
    try:
        body.Tip = t
    except Exception:
        pass
    doc.recompute()
    t.Label = _tr("Mirror (symmetry)")
    _msg(_tr(
        "Revolved the body 180 degrees around the symmetry axis "
        "(2 occurrences)."))
    return True


def _point_symmetry(body, doc, ref):
    shape = body.Shape
    if shape is None or shape.isNull():
        _msg(_tr("The body has no solid to mirror."), error=True)
        return False
    c = ref.Placement.Base
    s = shape.mirror(FreeCAD.Vector(c.x, 0, 0), FreeCAD.Vector(1, 0, 0))
    s = s.mirror(FreeCAD.Vector(0, c.y, 0), FreeCAD.Vector(0, 1, 0))
    s = s.mirror(FreeCAD.Vector(0, 0, c.z), FreeCAD.Vector(0, 0, 1))
    f = doc.addObject("Part::Feature", _TRANSFORM_NAME)
    f.Label = "Symmetry (point)"
    f.Shape = s
    doc.recompute()
    _msg(_tr(
        "Point symmetry creates a static copy that does not update when "
        "you edit the solid."))
    return True


# ---------------------------------------------------------------- manual sync


def find_reference(doc):
    """Find the addon symmetry reference datum in the document.

    The datum the panel is currently working on (if any) wins, so new mirror
    operations always use the reference the user just created. The scan falls
    back to the first addon datum (plane / line / point) in the document, or
    None when the user has not created one yet (single feature mirror, no
    reference chosen)."""
    if doc is None:
        return None
    if _active_ref_name:
        o = doc.getObject(_active_ref_name)
        if o is not None:
            try:
                if o.TypeId in ("Part::DatumPlane", "PartDesign::Plane",
                                "Part::DatumLine", "PartDesign::Line",
                                "Part::DatumPoint", "PartDesign::Point"):
                    return o
            except Exception:
                pass
    for o in doc.Objects:
        if o is None:
            continue
        n = o.Name
        if n == _REF_NAME or n == _TRANSFORM_NAME \
                or n.startswith(_REF_NAME) or n.startswith(_TRANSFORM_NAME):
            try:
                if o.TypeId in ("Part::DatumPlane", "PartDesign::Plane",
                                "Part::DatumLine", "PartDesign::Line",
                                "Part::DatumPoint", "PartDesign::Point"):
                    return o
            except Exception:
                pass
    for o in doc.Objects:
        if o is None:
            continue
        try:
            if o.TypeId in ("PartDesign::Plane", "PartDesign::Line",
                            "PartDesign::Point"):
                return o
        except Exception:
            pass
    return None


def hide_reference(doc):
    """Hide the addon symmetry reference datum currently in use (the active
    one) in the 3D view, so closing the symmetry panel leaves a clean scene.
    Other datums are not touched."""
    _set_reference_visibility(doc, False)


def show_reference(doc):
    """Show again the addon symmetry reference datum currently in use, used
    when the symmetry panel is opened while working on the body."""
    _set_reference_visibility(doc, True)


def _set_reference_visibility(doc, visible):
    if doc is None:
        return
    target = None
    if _active_ref_name:
        target = doc.getObject(_active_ref_name)
    if target is not None:
        try:
            target.ViewObject.Visibility = visible
        except Exception:
            pass
        return
    for o in doc.Objects:
        if o is None:
            continue
        n = o.Name
        if n == _REF_NAME or n.startswith(_REF_NAME):
            try:
                o.ViewObject.Visibility = visible
                break
            except Exception:
                pass


def sync_visibility(doc_name, body_name, tip_name):
    """Hide the real PartDesign features of the body (Pad, Pocket, ...) except
    the Tip, and make the Tip visible. Datum and addon reference objects are
    left untouched. Used to keep the 3D view clean when the mirror is active."""
    try:
        doc = _get_document(doc_name)
        if doc is None:
            return
        body = doc.getObject(body_name)
        tip = doc.getObject(tip_name)
        if body is None or tip is None:
            return
        for f in (getattr(body, "Group", []) or []):
            if f is None or f.Name == tip.Name or not _is_transform_feature(f):
                continue
            try:
                if f.ViewObject is not None:
                    f.ViewObject.Visibility = False
            except Exception:
                pass
        try:
            if tip.ViewObject is not None:
                tip.ViewObject.Visibility = True
        except Exception:
            pass
        try:
            if body.ViewObject is not None:
                body.ViewObject.Visibility = True
        except Exception:
            pass
        try:
            import FreeCADGui as Gui
            Gui.updateGui()
        except Exception:
            pass
    except Exception:
        pass


def _get_document(name):
    try:
        return FreeCAD.getDocument(name)
    except Exception:
        return None


def _is_own_name(name):
    """The addon's own reference / transform objects are not real features."""
    return name == _REF_NAME or name == _TRANSFORM_NAME \
        or name.startswith(_REF_NAME) or name.startswith(_TRANSFORM_NAME)


def _find_transform(body):
    """The live symmetry transform feature (a PartDesign::Mirrored or
    PartDesign::PolarPattern)."""
    for f in (getattr(body, "Group", []) or []):
        if f is None:
            continue
        if f.Name.startswith(_TRANSFORM_NAME) \
                and getattr(f, "SymmetryTransform", False):
            return f
    return None


def _real_features(body):
    """Body features that can be mirrored, in tree order, skipping the
    addon's own reference and transform objects."""
    out = []
    for f in (getattr(body, "Group", []) or []):
        if f is None or _is_own_name(f.Name):
            continue
        if _is_transform_feature(f):
            out.append(f)
    return out


def _reference_of(transform):
    """The datum the transform mirrors around (plane or axis)."""
    try:
        if getattr(transform, "MirrorPlane", None):
            return transform.MirrorPlane[0]
    except Exception:
        pass
    try:
        if getattr(transform, "Axis", None):
            return transform.Axis[0]
    except Exception:
        pass
    return None


def mirror_feature(doc, body, ref, feat):
    """Mirror a single feature around the reference datum.

    A new PartDesign transform (PartDesign::Mirrored or PolarPattern) is
    created on top of the body with only `feat` as Originals. Existing
    features and the previous symmetry transform (if any) are left untouched,
    so the body tree never gets re-arranged and edge/face references keep
    working (this is the flow validated by the user macro).

    Idempotent: if a transform mirroring `feat` already exists no duplicate
    is created. Returns True on success (or when already mirrored)."""
    if body is None or doc is None or ref is None or feat is None:
        return False
    # if feat is already mirrored by an existing transform -> no duplicate
    for f in (getattr(body, "Group", []) or []):
        if f is None or not f.Name.startswith(_TRANSFORM_NAME):
            continue
        if not getattr(f, "SymmetryTransform", False):
            continue
        try:
            if feat in list(f.Originals or []):
                return True
        except Exception:
            pass
    try:
        if ref.TypeId in ("Part::DatumPlane", "PartDesign::Plane"):
            t = body.newObject("PartDesign::Mirrored", _TRANSFORM_NAME)
            t.addProperty("App::PropertyBool", "SymmetryTransform",
                          _PROP_GROUP, "")
            t.SymmetryTransform = True
            t.TransformMode = "Features"
            t.Originals = [feat]
            t.MirrorPlane = (ref, "Original")
        elif ref.TypeId in ("Part::DatumLine", "PartDesign::Line"):
            t = body.newObject("PartDesign::PolarPattern", _TRANSFORM_NAME)
            t.addProperty("App::PropertyBool", "SymmetryTransform",
                          _PROP_GROUP, "")
            t.SymmetryTransform = True
            t.Originals = [feat]
            t.Axis = (ref, "Original")
            t.Angle = 180
            t.Occurrences = 2
        else:
            _msg(_tr("Point symmetry is not supported for a single "
                     "operation."), error=True)
            return False
    except Exception as exc:
        _msg(_tr("Could not mirror the last operation: {}").format(exc),
             error=True)
        return False
    try:
        body.Tip = t
    except Exception:
        pass
    try:
        doc.recompute()
    except Exception:
        pass
    t.Label = _tr("Mirror (symmetry)")
    try:
        st = t.Shape
        valid = st is not None and not st.isNull() and st.isValid() and st.Solids
    except Exception:
        valid = False
    if not valid:
        _msg(_tr("Mirror failed: the mirrored shape is invalid."), error=True)
        return False
    _msg(_tr("Mirrored the last operation around the symmetry plane "
             "({}).").format(feat.Label))
    return True


def mirror_last_operation(doc, body):
    """Mirror the last real feature in the tree.

    A new symmetry transform mirroring only the latest feature is appended to
    the body (the flow proven by the user macro): existing features and any
    previous symmetry transform are never touched, so edge/face references
    cannot break.  Returns True when the mirror reflects the latest feature.

    If the last feature is already mirrored by an existing transform the call
    is a safe no-op (returns True without creating a duplicate)."""
    if body is None or doc is None:
        return False
    ref = find_reference(doc)
    if ref is None:
        _msg(_tr("No symmetry reference found."), error=True)
        return False
    real = _real_features(body)
    if not real:
        _msg(_tr("No PartDesign features to mirror."), error=True)
        return False
    last = real[-1]
    if _is_own_name(last.Name):
        return False
    for f in (getattr(body, "Group", []) or []):
        if f is None or not f.Name.startswith(_TRANSFORM_NAME):
            continue
        if not getattr(f, "SymmetryTransform", False):
            continue
        try:
            if last in list(f.Originals or []):
                return True
        except Exception:
            pass
    ok = mirror_feature(doc, body, ref, last)
    if ok:
        sync_visibility(doc.Name, body.Name, body.Tip.Name if body.Tip else None)
    return ok