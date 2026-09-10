# -*- coding: utf-8 -*-
"""Rib feature core geometry and feature classes.

A rib is a stiffening plate created from a sketch profile (open or closed wire)
by extruding the profile perpendicular to the sketch plane by a given thickness.

The sketch defines the rib's mid-surface outline.  Thickness is applied
symmetrically (midplane) or on one side, perpendicular to the sketch plane,
then fused with the body.

PartDesign removed the native Rib tool in 1.0; this re-implements it.
"""

import time

import FreeCAD
import Part

try:
    from .translations import tr as _tr
except ImportError:
    from translations import tr as _tr


# =============================================================================
# Throttled warning (shared with pipe_core pattern)
# =============================================================================

_WARN_STATE = {"key": "", "stamp": 0.0}


def _warn_throttled(msg, cooldown=3.0):
    now = time.time()
    if msg == _WARN_STATE["key"] and now - _WARN_STATE["stamp"] < cooldown:
        return
    _WARN_STATE["key"] = msg
    _WARN_STATE["stamp"] = now
    FreeCAD.Console.PrintWarning(msg)


# =============================================================================
# Geometry helpers
# =============================================================================

def _get_sketch_normal(sketch):
    """Return the sketch plane outward normal in global coordinates."""
    placement = sketch.Placement
    local_normal = FreeCAD.Vector(0, 0, 1)
    return placement.Rotation.multVec(local_normal)


def _ensure_closed_wire(wire):
    """If *wire* is open, close it by connecting its endpoints."""
    if wire.isClosed():
        return wire
    verts = wire.Vertexes
    if len(verts) < 2:
        return wire
    closing = Part.makeLine(verts[0].Point, verts[-1].Point)
    return Part.Wire(wire.Edges + [closing])


def _refine(shape):
    if shape is None or shape.isNull() or not shape.isValid():
        return shape
    try:
        return shape.removeSplitter()
    except Exception:
        return shape


# =============================================================================
# Public geometry builder
# =============================================================================

def build_rib_from_sketch(sketch, thickness, midplane=True, reversed=False):
    """Build a rib solid from a sketch.

    Parameters
    ----------
    sketch : Part::SketchObject
        The sketch whose wire defines the rib mid-surface outline.
    thickness : float
        Rib thickness (mm).  Applied perpendicular to the sketch plane.
    midplane : bool
        If True the thickness extends equally on both sides of the sketch
        plane (default).  If False it extends only on the positive normal
        side.
    reversed : bool
        Flip the normal direction (applies before midplane logic).

    Returns
    -------
    Part.Shape
        A solid rib shape (not yet fused with any body).

    Raises
    ------
    ValueError
        If the sketch is empty or the thickness is not positive.
    """
    t = float(thickness)
    if t <= 0:
        raise ValueError(_tr("Thickness must be positive"))

    normal = _get_sketch_normal(sketch)
    if reversed:
        normal = -normal

    edges = sketch.Shape.Edges
    if not edges:
        raise ValueError(_tr("The sketch is empty"))

    wire = Part.Wire(edges)

    # Closed wire → face directly; open wire → close with a segment between
    # the two endpoints so that Part.Face succeeds.  The closing segment is
    # harmless: the rib shape is trimmed by the body when fused.
    closed_wire = _ensure_closed_wire(wire)
    if closed_wire is None or len(closed_wire.Edges) < 2:
        raise ValueError(_tr(
            "The profile is degenerate: it has no area to extrude. "
            "Draw a closed profile or an open profile with more than one edge."))
    try:
        face = Part.Face(closed_wire)
    except Exception:
        face = None
    if face is None or not face.isValid() or abs(face.Area) < 1e-7:
        raise ValueError(_tr(
            "The profile is degenerate: it has no area to extrude. "
            "A single straight line cannot form a rib; use at least two "
            "connected edges, an arc, or a closed profile."))

    # Extrude along the normal by the full thickness, then centre.
    prism = face.extrude(normal * t)
    if midplane:
        prism.translate(-normal * (t / 2.0))

    return prism


# =============================================================================
# Selection helpers (mirrors pipe_core pattern)
# =============================================================================

def _collect_sketch_from_selection():
    """Return (sketch_or_None, body_or_None) from the current selection."""
    import FreeCADGui as Gui

    sketch = None
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
    return sketch, target_body


def _parent_body(obj, doc):
    """Return the PartDesign body owning *obj*, if any."""
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
    """Set the FormsViewProvider without crashing in console mode."""
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
    """Copy colour/material look from one view object to another."""
    if src_vobj is None or dst_vobj is None:
        return
    for prop in ("ShapeAppearance", "DiffuseColor", "Transparency"):
        if not hasattr(src_vobj, prop) or not hasattr(dst_vobj, prop):
            continue
        try:
            setattr(dst_vobj, prop, getattr(src_vobj, prop))
        except Exception:
            pass


# =============================================================================
# Feature proxy classes
# =============================================================================

def _setup_rib_properties(obj):
    if not hasattr(obj, "SketchRef"):
        obj.addProperty("App::PropertyLink", "SketchRef", "Rib")
    if not hasattr(obj, "Thickness"):
        obj.addProperty("App::PropertyLength", "Thickness", "Rib")
        obj.Thickness = 5.0
    if not hasattr(obj, "Midplane"):
        obj.addProperty("App::PropertyBool", "Midplane", "Rib")
        obj.Midplane = True
    if not hasattr(obj, "Reversed"):
        obj.addProperty("App::PropertyBool", "Reversed", "Rib")
        obj.Reversed = False
    if not hasattr(obj, "Refine"):
        obj.addProperty("App::PropertyBool", "Refine", "Rib")
        obj.Refine = True


class RibFeature:
    """Standalone parametric rib (no body required)."""

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "RibFeature"
        _setup_rib_properties(obj)

    def execute(self, fp):
        try:
            sk = fp.SketchRef
            if sk is None or sk.Shape is None or not sk.Shape.Edges:
                fp.Shape = Part.Shape()
                return
            shape = build_rib_from_sketch(
                sk, float(fp.Thickness), fp.Midplane, fp.Reversed)
            fp.Shape = _refine(shape) if fp.Refine else shape
        except Exception as e:
            FreeCAD.Console.PrintError("RibFeature.execute error: {}\n".format(e))
            fp.Shape = Part.Shape()


class AdditiveRibFeature:
    """PartDesign additive rib: rib fused with the body tip."""

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "AdditiveRibFeature"
        _setup_rib_properties(obj)

    def execute(self, fp):
        try:
            sk = fp.SketchRef
            if sk is None or sk.Shape is None or not sk.Shape.Edges:
                fp.Shape = Part.Shape()
                return
            raw = build_rib_from_sketch(
                sk, float(fp.Thickness), fp.Midplane, fp.Reversed)
            base = getattr(fp, "BaseFeature", None)
            if base is not None and base.Shape is not None and not base.Shape.isNull():
                shape = base.Shape.fuse(raw)
            else:
                shape = raw
            fp.Shape = _refine(shape) if fp.Refine else shape
        except Exception as e:
            FreeCAD.Console.PrintError(
                "AdditiveRibFeature.execute error: {}\n".format(e))
            fp.Shape = Part.Shape()


class SubtractiveRibFeature:
    """PartDesign subtractive rib: rib removed from the body tip."""

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "SubtractiveRibFeature"
        _setup_rib_properties(obj)

    def execute(self, fp):
        try:
            sk = fp.SketchRef
            if sk is None or sk.Shape is None or not sk.Shape.Edges:
                fp.Shape = Part.Shape()
                return
            raw = build_rib_from_sketch(
                sk, float(fp.Thickness), fp.Midplane, fp.Reversed)
            base = getattr(fp, "BaseFeature", None)
            if base is not None and base.Shape is not None and not base.Shape.isNull():
                shape = base.Shape.cut(raw)
            else:
                FreeCAD.Console.PrintError(
                    "SubtractiveRibFeature needs an existing body to subtract from.\n")
                shape = Part.Shape()
            fp.Shape = _refine(shape) if fp.Refine else shape
        except Exception as e:
            FreeCAD.Console.PrintError(
                "SubtractiveRibFeature.execute error: {}\n".format(e))
            fp.Shape = Part.Shape()


# =============================================================================
# Public command
# =============================================================================

def create_rib(subtractive=False):
    """Create a rib from a selected sketch.

    The sketch must be selected before calling this function.  A small task
    panel lets the user adjust thickness, midplane and reversed before
    committing.
    """
    import FreeCADGui as Gui

    doc = FreeCAD.ActiveDocument
    if doc is None:
        FreeCAD.Console.PrintError(_tr("No active document") + "\n")
        return

    sketch, sel_body = _collect_sketch_from_selection()
    if sketch is None:
        FreeCAD.Console.PrintMessage(
            _tr("Select a sketch as the rib profile.") + "\n")
        return
    if not sketch.Shape.Edges:
        FreeCAD.Console.PrintError(_tr("The selected sketch is empty.") + "\n")
        return

    # Find target body
    body = sel_body
    if body is None:
        body = _parent_body(sketch, doc)
    if body is None:
        try:
            body = Gui.activeBody()
        except Exception:
            body = None
    if body is None:
        bodies = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
        if len(bodies) == 1:
            body = bodies[0]

    from .RibDialog import RibPanel

    def _shape_of(thickness, midplane, reversed, mode="tool"):
        try:
            raw = build_rib_from_sketch(sketch, thickness, midplane, reversed)
            if mode != "tool" and body is not None:
                tip = getattr(body, "Tip", None)
                if tip is not None and tip.Shape is not None and not tip.Shape.isNull():
                    try:
                        if subtractive:
                            raw = tip.Shape.cut(raw)
                        else:
                            raw = tip.Shape.fuse(raw)
                    except Exception:
                        pass
            return _refine(raw)
        except Exception:
            return None

    hidden_tip = {"obj": None, "was": True}

    def _hide_body_for_preview():
        if body is None:
            return
        tip = getattr(body, "Tip", None)
        if tip is None:
            return
        nano = str(tip.Name)
        if hidden_tip["obj"] is not None:
            return
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
        if tip is None or not restore:
            return
        try:
            tip.ViewObject.Visibility = hidden_tip["was"]
        except Exception:
            pass

    def _remove_preview(restore=True):
        pv = doc.getObject("RibPreview")
        if pv is not None:
            try:
                doc.removeObject(pv.Name)
            except Exception:
                pass
        _restore_body_visibility(restore)

    def _on_change(thickness, midplane, reversed, mode="tool"):
        shp = _shape_of(thickness, midplane, reversed, mode)
        pv = doc.getObject("RibPreview")
        if shp is None:
            _remove_preview()
            return
        if pv is None:
            pv = doc.addObject("Part::Feature", "RibPreview")
            _set_view_object_ok(pv)
            try:
                pv.ViewObject.Selectable = False
            except Exception:
                pass
        if mode == "result":
            _hide_body_for_preview()
        else:
            _restore_body_visibility()
        try:
            if mode == "result":
                pv.ViewObject.ShapeColor = (0.7, 0.7, 0.7, 1.0)
                pv.ViewObject.Transparency = 0
            elif subtractive:
                pv.ViewObject.ShapeColor = (0.62, 0.40, 0.80, 1.0)
                pv.ViewObject.Transparency = 40
            else:
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

    def _on_finish(thickness, midplane, reversed, mode="tool"):
        newfeat = None
        try:
            # validate the profile before creating a possibly-broken feature
            build_rib_from_sketch(sketch, thickness, midplane, reversed)
        except Exception as e:
            FreeCAD.Console.PrintError(_tr("Rib: {}").format(e) + "\n")
            return
        try:
            if body is not None:
                old_tip = getattr(body, "Tip", None)
                if subtractive:
                    feat = doc.addObject(
                        "PartDesign::FeatureSubtractivePython", "RibCut")
                    SubtractiveRibFeature(feat)
                else:
                    feat = doc.addObject(
                        "PartDesign::FeatureAdditivePython", "Rib")
                    AdditiveRibFeature(feat)
                feat.SketchRef = sketch
                feat.Thickness = thickness
                feat.Midplane = midplane
                feat.Reversed = reversed
                body.addObject(feat)
                _set_view_object_ok(feat)
                doc.recompute()
                try:
                    body.Tip = feat
                except Exception:
                    pass
                newfeat = feat
                doc.recompute()
                try:
                    if old_tip is not None and old_tip.ViewObject is not None:
                        _copy_appearance(old_tip.ViewObject, newfeat.ViewObject)
                except Exception:
                    pass
                if subtractive:
                    FreeCAD.Console.PrintMessage(
                        _tr("Subtractive rib removed from '{}'.").format(
                            body.Label) + "\n")
                else:
                    FreeCAD.Console.PrintMessage(
                        _tr("Additive rib added to '{}'.").format(
                            body.Label) + "\n")
            else:
                if subtractive:
                    FreeCAD.Console.PrintError(
                        _tr("Subtractive rib needs a PartDesign body to cut.") + "\n")
                    return
                obj = doc.addObject("Part::FeaturePython", "Rib")
                RibFeature(obj)
                obj.SketchRef = sketch
                obj.Thickness = thickness
                obj.Midplane = midplane
                obj.Reversed = reversed
                _set_view_object_ok(obj)
                newfeat = obj
                doc.recompute()
                FreeCAD.Console.PrintMessage(_tr("Rib created.") + "\n")
        finally:
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

    try:
        if Gui.Control.activeDialog():
            Gui.Control.closeDialog()
    except Exception:
        pass
    Gui.Control.showDialog(RibPanel(_on_change, _on_finish, _on_cancel))
