# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Automatic symmetry for PartDesignUpgrade.

A small checkable toolbar button ("Automatic symmetry") toggles the automatic
mirror on or off. The mirror uses the reference chosen in the "Mirror
(Symmetry)" task panel (plane XY / XZ / YZ, axis X / Y / Z, point) together
with its offsets. When enabled, the mirrored solid is computed by a parametric
Part::FeaturePython object: it re-reflects the current body shape after every
change to the body, so every new pad/pocket is mirrored automatically.

Offsets are measured from the body centre. A plane has a single movement along
its normal, an axis has two independent perpendicular movements and a point has
three (X, Y, Z). Planes are mirrored with Shape.mirror; a 180 degree axial
rotation is expressed as two reflections across perpendicular planes through
the axis; the point inversion is three mirror reflections.
"""

import FreeCAD
import Part

from .translations import tr as _tr

_FEATURE_NAME = "Symmetry"
_REF_NAME = "SymmetryRef"

_last_choice = {"kind": "plane", "target": "XY", "offset": 0.0}
_auto_on = False


def set_choice(kind, target, offset):
    """Remember the reference chosen in the mirror task panel. When the
    automatic feature already exists and is enabled, it follows the choice.
    offset is a float (plane), a 2-tuple (axis) or a 3-tuple (point)."""
    global _last_choice
    if kind not in ("plane", "axis", "point"):
        kind = "plane"
    _last_choice = {"kind": kind, "target": target, "offset": offset}
    feat = _existing_feature()
    if feat is not None and getattr(feat, "Enabled", False):
        _apply_choice(feat)


def is_active():
    return _auto_on


def _existing_feature(doc=None):
    if doc is None:
        doc = FreeCAD.ActiveDocument
    if doc is None:
        return None
    return doc.getObject(_FEATURE_NAME)


def _planes_axes_point(kind, target):
    planes = (False, False, False)
    axes = (False, False, False)
    point = False
    if kind == "plane":
        planes = (target == "XY", target == "XZ", target == "YZ")
    elif kind == "axis":
        axes = (target == "X", target == "Y", target == "Z")
    else:
        point = True
    return planes, axes, point


def _apply_choice(feat):
    kind = _last_choice["kind"]
    target = _last_choice["target"]
    offset = _last_choice["offset"]
    planes, axes, point = _planes_axes_point(kind, target)
    set_refs(feat, planes, axes, point, offset, enabled=True)
    doc = feat.Document
    body = feat.Src
    if body is not None:
        _update_reference(body, planes, axes, point, offset)
    try:
        doc.recompute()
    except Exception:
        pass


def toggle_auto(doc, body):
    """Flip the automatic symmetry state. Returns the new state (True = on)."""
    global _auto_on
    _auto_on = not _auto_on
    if _auto_on:
        feat = ensure_feature(doc, body)
        _apply_choice(feat)
    else:
        feat = _existing_feature(doc)
        if feat is not None:
            feat.Enabled = False
        _update_reference(body, (False, False, False),
                          (False, False, False), False, 0.0)
        if body is not None and body.Document is not None:
            try:
                body.Document.recompute()
            except Exception:
                pass
    return _auto_on


def set_active(doc, body, on):
    """Enable or disable automatic symmetry around the last chosen reference."""
    global _auto_on
    _auto_on = bool(on)
    if _auto_on:
        feat = ensure_feature(doc, body)
        _apply_choice(feat)
    else:
        feat = _existing_feature(doc)
        if feat is not None:
            feat.Enabled = False
        _update_reference(body, (False, False, False),
                          (False, False, False), False, 0.0)
        if body is not None and body.Document is not None:
            try:
                body.Document.recompute()
            except Exception:
                pass
    return _auto_on


def _update_reference(body, planes, axes, point, offset):
    """Show a datum plane/line/point inside the body matching the active
    selection (first selected plane, else first selected axis, else point).
    Removes the datum when nothing is selected. offset may be a float, a
    2-tuple (axis) or a 3-tuple (point)."""
    if body is None:
        return
    doc = body.Document
    ref = doc.getObject(_REF_NAME)
    try:
        from . import symmetry as _sym
        if ref is not None and _sym._is_referenced_by_transform(doc, ref):
            # The datum belongs to a mirror that was already built: never
            # delete it nor re-point it. The preview uses its own copy.
            ref = None
    except Exception:
        pass
    if not any(list(planes) + list(axes) + [point]):
        if ref is not None:
            try:
                doc.removeObject(_REF_NAME)
            except Exception:
                try:
                    body.removeObject(ref)
                except Exception:
                    pass
        return

    shape = body.Shape
    if shape is None or shape.isNull():
        if ref is not None:
            try:
                doc.removeObject(_REF_NAME)
            except Exception:
                try:
                    body.removeObject(ref)
                except Exception:
                    pass
        return
    c = shape.BoundBox.Center
    inv = body.Placement.inverse()

    if any(planes):
        target = "XY"
        if planes[1]:
            target = "XZ"
        if planes[2]:
            target = "YZ"
        new_type = "PartDesign::Plane"
        off = float(offset) if not _is_seq(offset) else 0.0
        if target == "XY":
            base = FreeCAD.Vector(c.x, c.y, c.z + off)
            rot = FreeCAD.Rotation()
        elif target == "XZ":
            base = FreeCAD.Vector(c.x, c.y + off, c.z)
            rot = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -90)
        else:  # YZ
            base = FreeCAD.Vector(c.x + off, c.y, c.z)
            rot = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90)
        box = shape.BoundBox
        size_kind = "plane"
    elif any(axes):
        target = "X" if axes[0] else ("Y" if axes[1] else "Z")
        new_type = "PartDesign::Line"
        if _is_seq(offset):
            d1 = float(_seq0(offset, 0))
            d2 = float(_seq0(offset, 1))
        else:
            d1 = float(offset)
            d2 = 0.0
        moves = {"X": ("Y", "Z"), "Y": ("X", "Z"), "Z": ("X", "Y")}[target]
        if "Y" in moves:
            pass
        lateral = {"X": (0, 1, 0), "Y": (1, 0, 0), "Z": (1, 0, 0)}[target]
        base = c + FreeCAD.Vector(*lateral) * d1
        if len(moves) == 2:
            second = {"X": (0, 0, 1), "Y": (0, 0, 1), "Z": (0, 1, 0)}[target]
            base = base + FreeCAD.Vector(*second) * d2
        rot = {"X": FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90),
               "Y": FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), -90),
               "Z": FreeCAD.Rotation()}[target]
        box = shape.BoundBox
        size_kind = "line"
    else:
        new_type = "PartDesign::Point"
        if _is_seq(offset) and len(offset) >= 3:
            dx, dy, dz = (float(offset[0]), float(offset[1]),
                          float(offset[2]))
        else:
            dx, dy, dz = 0.0, 0.0, float(offset)
        base = c + FreeCAD.Vector(dx, dy, dz)
        rot = FreeCAD.Rotation()
        box = None
        size_kind = None

    if ref is not None and ref.TypeId != new_type:
        try:
            doc.removeObject(_REF_NAME)
        except Exception:
            try:
                body.removeObject(ref)
            except Exception:
                pass
        ref = None
    if ref is None:
        ref = body.newObject(new_type, _REF_NAME)
        ref.MapMode = "Deactivated"
    ref.Placement = FreeCAD.Placement(inv * base, rot)
    try:
        from . import symmetry as _sym
        if size_kind == "plane" and box is not None:
            ref.ResizeMode = "Manual"
            length, width = _sym._datum_extents(box, rot)
            ref.Length = length
            ref.Width = width
        elif size_kind == "line" and box is not None:
            ref.ResizeMode = "Manual"
            ref.Length = _sym._datum_extents(box, rot, length_only=True)
    except Exception:
        pass
    try:
        ref.ViewObject.Visibility = True
    except Exception:
        pass


def _is_seq(v):
    return isinstance(v, (tuple, list))


def _seq0(v, i):
    try:
        return v[i]
    except Exception:
        return 0.0


class _SymmetryFeature:
    """FeaturePython proxy: reflects the source body shape on recompute."""

    def __init__(self, obj):
        obj.Proxy = self
        self._auto_sym = True
        self._executing = False
        props = (("App::PropertyBool", "Enabled"),
                 ("App::PropertyLink", "Src"),
                 ("App::PropertyBool", "RefXY"),
                 ("App::PropertyBool", "RefXZ"),
                 ("App::PropertyBool", "RefYZ"),
                 ("App::PropertyBool", "AxisX"),
                 ("App::PropertyBool", "AxisY"),
                 ("App::PropertyBool", "AxisZ"),
                 ("App::PropertyBool", "RefPoint"),
                 ("App::PropertyFloat", "OffsetX"),
                 ("App::PropertyFloat", "OffsetY"),
                 ("App::PropertyFloat", "OffsetZ"))
        docs = (("Enabled", "Automatically mirror the body"),
                ("Src", "Body to mirror"),
                ("RefXY", "Mirror about the XY plane"),
                ("RefXZ", "Mirror about the XZ plane"),
                ("RefYZ", "Mirror about the YZ plane"),
                ("AxisX", "Rotate 180 deg about the X axis"),
                ("AxisY", "Rotate 180 deg about the Y axis"),
                ("AxisZ", "Rotate 180 deg about the Z axis"),
                ("RefPoint", "Invert through a point"),
                ("OffsetX", "Offset along X from the body centre"),
                ("OffsetY", "Offset along Y from the body centre"),
                ("OffsetZ", "Offset along Z from the body centre"))
        for (ptype, pname), (_n, doc) in zip(props, docs):
            try:
                obj.getPropertyByName(pname)
                exists = True
            except Exception:
                exists = False
            if not exists:
                obj.addProperty(ptype, pname, "Symmetry", _tr(doc))
        obj.Enabled = True
        for pn in ("OffsetX", "OffsetY", "OffsetZ"):
            try:
                setattr(obj, pn, 0.0)
            except Exception:
                pass

    def execute(self, obj):
        if self._executing:
            return
        src = obj.Src
        shape = src.Shape if src is not None else None
        if shape is None or shape.isNull():
            obj.Shape = None
            return
        if not getattr(obj, "Enabled", True) or not shape.Solids:
            obj.Shape = shape
            return
        self._executing = True
        try:
            obj.Shape = self._build_shape(shape, obj)
        finally:
            self._executing = False

    @staticmethod
    def _build_shape(shape, obj):
        c = shape.BoundBox.Center
        ox = getattr(obj, "OffsetX", 0.0) or 0.0
        oy = getattr(obj, "OffsetY", 0.0) or 0.0
        oz = getattr(obj, "OffsetZ", 0.0) or 0.0
        copies = []
        if getattr(obj, "RefXY", False):
            copies.append(shape.mirror(FreeCAD.Vector(0, 0, c.z + oz),
                                       FreeCAD.Vector(0, 0, 1)))
        if getattr(obj, "RefXZ", False):
            copies.append(shape.mirror(FreeCAD.Vector(0, c.y + oy, 0),
                                       FreeCAD.Vector(0, 1, 0)))
        if getattr(obj, "RefYZ", False):
            copies.append(shape.mirror(FreeCAD.Vector(c.x + ox, 0, 0),
                                       FreeCAD.Vector(1, 0, 0)))
        if getattr(obj, "AxisX", False):
            s = shape.mirror(FreeCAD.Vector(0, c.y + oy, 0),
                             FreeCAD.Vector(0, 1, 0))
            copies.append(s.mirror(FreeCAD.Vector(0, 0, c.z + oz),
                                   FreeCAD.Vector(0, 0, 1)))
        if getattr(obj, "AxisY", False):
            s = shape.mirror(FreeCAD.Vector(c.x + ox, 0, 0),
                             FreeCAD.Vector(1, 0, 0))
            copies.append(s.mirror(FreeCAD.Vector(0, 0, c.z + oz),
                                   FreeCAD.Vector(0, 0, 1)))
        if getattr(obj, "AxisZ", False):
            s = shape.mirror(FreeCAD.Vector(c.x + ox, 0, 0),
                             FreeCAD.Vector(1, 0, 0))
            copies.append(s.mirror(FreeCAD.Vector(0, c.y + oy, 0),
                                   FreeCAD.Vector(0, 1, 0)))
        if getattr(obj, "RefPoint", False):
            s = shape.mirror(FreeCAD.Vector(c.x + ox, 0, 0),
                             FreeCAD.Vector(1, 0, 0))
            s = s.mirror(FreeCAD.Vector(0, c.y + oy, 0),
                         FreeCAD.Vector(0, 1, 0))
            copies.append(s.mirror(FreeCAD.Vector(0, 0, c.z + oz),
                                   FreeCAD.Vector(0, 0, 1)))
        if not copies:
            return shape
        fused = shape
        for c in copies:
            fused = fused.fuse(c)
        try:
            fused = fused.removeSplitter()
        except Exception:
            pass
        return fused

    def onChanged(self, obj, prop):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


def ensure_feature(doc, body):
    """Return the automatic symmetry feature for the body, creating or
    relinking it as needed."""
    feat = doc.getObject(_FEATURE_NAME)
    if feat is None:
        feat = doc.addObject("Part::FeaturePython", _FEATURE_NAME)
        _SymmetryFeature(feat)
    elif not getattr(feat.Proxy, "_auto_sym", False):
        feat.Proxy = _SymmetryFeature(feat)
    if feat.Src is not body:
        feat.Src = body
    return feat


def _set_offsets(feat, planes, axes, point, offset):
    """Store the offsets. offset is a float, 2-tuple or 3-tuple; the value is
    mapped to the directions relevant for the first selected reference."""
    if _is_seq(offset) and len(offset) >= 3:
        ox, oy, oz = (float(offset[0]), float(offset[1]), float(offset[2]))
    elif _is_seq(offset) and len(offset) == 2:
        ox, oy, oz = 0.0, 0.0, 0.0
        if any(planes):
            ox = float(offset[0])
            oz = float(offset[1]) if len(offset) > 1 else 0.0
        elif any(axes):
            if axes[0]:  # axis X -> moves along Y and Z
                oy, oz = float(offset[0]), float(offset[1])
            elif axes[1]:  # axis Y -> moves along X and Z
                ox, oz = float(offset[0]), float(offset[1])
            elif axes[2]:  # axis Z -> moves along X and Y
                ox, oy = float(offset[0]), float(offset[1])
    else:
        ox, oy, oz = 0.0, 0.0, 0.0
        off = float(offset) if not _is_seq(offset) else 0.0
        if any(planes) or point:
            ox, oy, oz = 0.0, 0.0, 0.0
            if any(planes):
                if planes[0]:  # XY
                    oz = off
                elif planes[1]:  # XZ
                    oy = off
                elif planes[2]:  # YZ
                    ox = off
            else:  # point
                oz = off
        elif any(axes):
            if axes[0]:
                oy = off
            else:
                ox = off
    setattr(feat, "OffsetX", ox)
    setattr(feat, "OffsetY", oy)
    setattr(feat, "OffsetZ", oz)


def set_refs(feat, planes, axes, point, offset, enabled=True):
    """Configure the references; planes/axes are iterables of booleans. offset
    may be a float, a 2-tuple (axis) or a 3-tuple (point)."""
    if feat is None:
        return
    setattr(feat, "RefXY", bool(planes[0]))
    setattr(feat, "RefXZ", bool(planes[1]))
    setattr(feat, "RefYZ", bool(planes[2]))
    setattr(feat, "AxisX", bool(axes[0]))
    setattr(feat, "AxisY", bool(axes[1]))
    setattr(feat, "AxisZ", bool(axes[2]))
    setattr(feat, "RefPoint", bool(point))
    _set_offsets(feat, planes, axes, point, offset)
    feat.Enabled = bool(enabled)
    try:
        feat.touch()
    except Exception:
        pass


def _active_body(doc):
    try:
        import FreeCADGui as Gui
        b = Gui.activeBody()
        if b is not None:
            return b
        for o in Gui.Selection.getSelection():
            if o is not None and o.TypeId == "PartDesign::Body":
                return o
    except Exception:
        pass
    body = None
    for o in doc.Objects:
        if o is not None and o.TypeId == "PartDesign::Body":
            if body is None:
                body = o
            else:
                return None
    return body