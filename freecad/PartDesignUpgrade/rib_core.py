# -*- coding: utf-8 -*-
"""Shared helpers for the PartDesignUpgrade feature core modules.

This module survived the removal of the old sketch-based Rib command: the
rib-between-faces core imports ``_refine``, ``_parent_body`` and
``_set_view_object_ok`` from here.
"""


def _refine(shape):
    if shape is None or shape.isNull() or not shape.isValid():
        return shape
    try:
        return shape.removeSplitter()
    except Exception:
        return shape


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