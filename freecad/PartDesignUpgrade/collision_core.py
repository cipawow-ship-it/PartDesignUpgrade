# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Core engine of the Collision Detector helper of PartDesignUpgrade.

While active, every solid body of the document is shown transparent and the
parts that interpenetrate are highlighted: every body that collides is
tinted yellow and a semi-transparent red volume is displayed for each
overlapping pair. Turning the detector off restores colour and transparency
of every body.

Recalculation is triggered by three independent mechanisms so that moving a
body (also inside an Assembly / App::Part container) always refreshes the
overlap preview:
  * a document observer (created/deleted/changed/recomputed) that schedules a
    debounced refresh;
  * a lightweight watchdog that every 1.5 s compares the global placement of
    every body and refreshes when something moved;
  * shapes are read through Part.getShape(), which resolves the full
    link/container placement chain, so bodies moved at the assembly level
    really change the reported geometry.
"""

import FreeCAD
import FreeCADGui as Gui
import Part

from PySide import QtCore

from .translations import tr as _tr

_CMD_NAME = "PartDesignUpgrade_Collision"
_GROUP_NAME = "PartDesignUpgrade_CollisionHighlight"
_TAG_PROP = "CDTag"
_TRANSPARENCY = 60
_OVERLAY_TRANSPARENCY = 30
_VOLUME_TOL_MM3 = 1e-6
_WATCHDOG_MS = 1500
_DEBOUNCE_MS = 600

_state = {
    "active": False,
    "refreshing": False,
    "doc": None,
    "rev": 0,
    "last_fp": None,
}
_saved = {}  # (doc_name, obj_name) -> (transparency, shapecolor)
_timer = None  # debounced refresh
_watchdog = None  # periodic placement check
_observer = None
_report_sink = None  # optional GUI dock callback: set_report(text)
_off_sink = None  # optional GUI callback: hide the dock when deactivated



def set_report_sink(fn):
    """Install a callback receiving the human-readable report text after every
    recalculation (None to uninstall). Used by the left side dock."""
    global _report_sink
    _report_sink = fn


def set_off_sink(fn):
    """Install a callback invoked when the detector is switched off (e.g. to
    hide the report dock)."""
    global _off_sink
    _off_sink = fn


def _notify_off():
    if _off_sink is None:
        return
    try:
        _off_sink()
    except Exception as exc:
        _err("PartDesignUpgrade: off sink failed: %s" % exc)


def _notify_report(text):
    if _report_sink is None:
        return
    try:
        _report_sink(text)
    except Exception as exc:
        _err("PartDesignUpgrade: report sink failed: %s" % exc)


def _report_text(bodies, hits):
    """Build the side-panel text: "no collision" or the colliding pairs with
    their overlap volumes."""
    if not hits:
        return _tr("No collisions ({0} bodies checked).").format(len(bodies))
    lines = [_tr("Collisions: {0}").format(len(hits))]
    for oi, oj, common in hits:
        lines.append("\u2022 {0} \u2229 {1}  \u2192  {2:.3f} mm\u00b3".format(
            _label(oi), _label(oj), common.Volume))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_active():
    return _state["active"]


def _msg(text):
    try:
        FreeCAD.Console.PrintMessage(text + "\n")
    except Exception:
        pass


def _err(text):
    try:
        FreeCAD.Console.PrintError(text + "\n")
    except Exception:
        pass


def _label(obj):
    return obj.Label if getattr(obj, "Label", "") else obj.Name


def _is_overlay(obj):
    try:
        return hasattr(obj, _TAG_PROP) and bool(getattr(obj, _TAG_PROP))
    except Exception:
        return False


def _copy_color(vo):
    try:
        return tuple(float(x) for x in vo.ShapeColor)
    except Exception:
        return None


def _get_attrib(vo, name, default=None):
    try:
        return getattr(vo, name)
    except Exception:
        return default


def _doc_alive(doc):
    try:
        return doc is not None and doc.Name in FreeCAD.listDocuments()
    except Exception:
        return False


def _has_solids(s):
    try:
        return s is not None and not s.isNull() and bool(s.Solids)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Collection and detection
# ---------------------------------------------------------------------------

def _is_container(o):
    try:
        t = o.TypeId
        return t == "App::Part" or t.startswith("Assembly::")
    except Exception:
        return False


def _safe_getshape(o):
    try:
        return Part.getShape(o)
    except Exception:
        return getattr(o, "Shape", None)


def _solid_list(s):
    try:
        if not _has_solids(s):
            return []
        seq = list(s.Solids)
        return list(seq) if seq else [s]
    except Exception:
        if _has_solids(s):
            return [s]
        return []


def _collect(doc):
    """Return [(obj, [Solid, ...]), ...] for every solid piece of the
    document. Shapes are resolved through Part.getShape() so the full
    link/container placement chain is honoured.

    To avoid double counting:
      * PartDesign features (which own a ``_Body``) are skipped: their
        PartDesign::Body already provides the final solid;
      * objects that live inside an App::Part / Assembly container are
        skipped, and instead each solid of the container (which honours the
        container placement) is collected.
    Our own overlay volumes are excluded."""
    container_solids = {}
    for o in doc.Objects:
        if o is None or _is_overlay(o) or o.Name == _GROUP_NAME:
            continue
        if not _is_container(o):
            continue
        sl = _solid_list(_safe_getshape(o))
        if sl:
            container_solids[o.Name] = (o, sl)

    skip_owned = bool(container_solids)
    found = []
    for o in doc.Objects:
        if o is None or _is_overlay(o) or o.Name == _GROUP_NAME or _is_container(o):
            continue
        if hasattr(o, "_Body"):
            continue
        sl = _solid_list(_safe_getshape(o))
        if not sl:
            continue
        if skip_owned:
            owned = False
            for c, _sl in container_solids.values():
                try:
                    if o in (c.OutList or []):
                        owned = True
                        break
                except Exception:
                    pass
            if owned:
                continue
        found.append((o, sl))

    for o, sl in container_solids.values():
        found.append((o, sl))
    return found


def _detect(bodies):
    """Return [(objA, objB, common_shape), ...] for every overlapping pair
    of individual solids. Contacts with zero volume are ignored."""
    hits = []
    n = len(bodies)
    for i in range(n):
        oi, si_list = bodies[i]
        for si in si_list:
            b1 = si.BoundBox
            for j in range(i + 1, n):
                oj, sj_list = bodies[j]
                for sj in sj_list:
                    b2 = sj.BoundBox
                    if (b1.XMin > b2.XMax or b2.XMin > b1.XMax
                            or b1.YMin > b2.YMax or b2.YMin > b1.YMax
                            or b1.ZMin > b2.ZMax or b2.ZMin > b1.ZMax):
                        continue
                    try:
                        common = si.common(sj)
                    except Exception as exc:
                        _err("PartDesignUpgrade: boolean common failed for %s / %s: %s"
                             % (_label(oi), _label(oj), exc))
                        continue
                    if common is None or common.isNull() or common.Volume <= _VOLUME_TOL_MM3:
                        continue
                    hits.append((oi, oj, common))
    return hits


# ---------------------------------------------------------------------------
# Visualisation
# ---------------------------------------------------------------------------

def _clear_overlays(doc):
    group = doc.getObject(_GROUP_NAME)
    if group is None:
        return
    for ov in list(group.OutList):
        try:
            doc.removeObject(ov.Name)
        except Exception:
            pass
    try:
        doc.removeObject(_GROUP_NAME)
    except Exception:
        pass


def _tint_targets(o):
    """Return the objects whose ViewProviders actually carry the visible
    colour/transparency of ``o``. Setting the colour on a PartDesign::Body
    shell does not reliably propagate to the displayed features, so the
    features themselves are coloured; for an App::Part / Assembly container
    the colour is applied to the solid objects inside it."""
    if o.TypeId == "PartDesign::Body":
        try:
            feats = list(o.Group or [])
        except Exception:
            feats = []
        return feats if feats else [o]
    if _is_container(o):
        out = []
        stack = list(o.OutList or [])
        seen = set()
        while stack:
            x = stack.pop(0)
            if x is None or x.Name in seen:
                continue
            seen.add(x.Name)
            if x.TypeId == "PartDesign::Body":
                try:
                    feats = list(x.Group or [])
                except Exception:
                    feats = []
                out.extend(feats if feats else [x])
            elif _is_container(x):
                try:
                    stack.extend(x.OutList or [])
                except Exception:
                    pass
            else:
                out.append(x)
        return out if out else [o]
    return [o]


def _set_visuals(doc, bodies, hits):
    _state["refreshing"] = True
    try:
        _clear_overlays(doc)
        # Every body of every colliding pair is tinted yellow.
        hit_names = set()
        for oi, oj, _s in hits:
            hit_names.add(oi.Name)
            hit_names.add(oj.Name)

        for o, _sl in bodies:
            is_hit = o.Name in hit_names
            for target in _tint_targets(o):
                vo = target.ViewObject
                if vo is None:
                    continue
                key = (doc.Name, target.Name)
                if key not in _saved:
                    _saved[key] = (
                        _get_attrib(vo, "Transparency"),
                        _copy_color(vo))
                try:
                    vo.Transparency = _TRANSPARENCY
                except Exception:
                    pass
                if is_hit:
                    try:
                        vo.ShapeColor = (1.0, 1.0, 0.0, 1.0)  # yellow: colliding body
                    except Exception:
                        pass
                elif key in _saved:
                    saved_color = _saved[key][1]
                    if saved_color is not None:
                        try:
                            vo.ShapeColor = saved_color
                        except Exception:
                            pass

        if hits:
            group = doc.getObject(_GROUP_NAME)
            if group is None:
                group = doc.addObject("App::DocumentObjectGroup", _GROUP_NAME)
            n_overlay = 0
            for oi, oj, common in hits:
                n_overlay += 1
                try:
                    _make_overlay(doc, group, oi, oj, common, n_overlay)
                except Exception as exc:
                    _err("PartDesignUpgrade: overlay creation failed for %s / %s: %s"
                         % (_label(oi), _label(oj), exc))
    finally:
        _state["refreshing"] = False


def _make_overlay(doc, group, oi, oj, common, n_overlay):
    ov = doc.addObject(
        "Part::Feature",
        "CD_%s_%s_%d_%d" % (oi.Name, oj.Name, _state["rev"], n_overlay))
    try:
        ov.addProperty(
            "App::PropertyString", _TAG_PROP, "PartDesignUpgrade",
            "Marker of collision overlay volumes")
        ov.CDTag = "overlay"
    except Exception:
        pass
    ov.Label = "%s \u2229 %s" % (_label(oi), _label(oj))
    ov.Shape = common
    group.addObject(ov)
    vvo = ov.ViewObject
    if vvo is not None:
        try:
            vvo.ShapeColor = (1.0, 0.0, 0.0, 1.0)  # red: overlap zone
        except Exception:
            pass
        try:
            vvo.Transparency = _OVERLAY_TRANSPARENCY
        except Exception:
            pass
        try:
            vvo.Visibility = True
        except Exception:
            pass


def _restore(doc):
    _state["refreshing"] = True
    try:
        _clear_overlays(doc)
        for key, (transparency, color) in list(_saved.items()):
            if key[0] != doc.Name:
                continue
            o = doc.getObject(key[1])
            if o is None:
                continue
            vo = o.ViewObject
            if vo is None:
                continue
            if color is not None:
                try:
                    vo.ShapeColor = color
                except Exception:
                    pass
            if transparency is not None:
                try:
                    vo.Transparency = transparency
                except Exception:
                    pass
    finally:
        _state["refreshing"] = False


# ---------------------------------------------------------------------------
# Refresh pipeline
# ---------------------------------------------------------------------------

def _current_doc():
    d = _state.get("doc")
    if _doc_alive(d):
        return d
    _state["doc"] = None
    d = FreeCAD.ActiveDocument
    if d is not None:
        _state["doc"] = d
        try:
            d.addObserver(_get_observer())
        except Exception:
            pass
    return d


def _refresh():
    if not _state["active"]:
        return
    doc = _current_doc()
    if doc is None:
        _err("PartDesignUpgrade: no active document.")
        return
    try:
        _state["rev"] += 1
        try:
            doc.recompute()
        except Exception:
            pass
        bodies = _collect(doc)
        hits = _detect(bodies)
        _set_visuals(doc, bodies, hits)
        _notify_report(_report_text(bodies, hits))
        _state["last_fp"] = _fingerprint(doc)
        if hits:
            _msg("PartDesignUpgrade: recalc #%d -> %d collision pair(s):"
                 % (_state["rev"], len(hits)))
            for oi, oj, common in hits:
                _msg("  - {0} \u2229 {1}  (overlap {2:.3g} mm^3)".format(
                    _label(oi), _label(oj), common.Volume))
        else:
            _msg("PartDesignUpgrade: recalc #%d -> no collision (%d bodies)."
                 % (_state["rev"], len(bodies)))
    except Exception as exc:
        _err("PartDesignUpgrade: refresh failed: %s" % exc)


def _fingerprint(doc):
    """Cheap fingerprint of the global placement of every solid body. Used by
    the watchdog to detect moves that the document observer might miss (e.g.
    parts moved at the assembly/container level)."""
    vals = []
    for o in doc.Objects:
        if o is None or _is_overlay(o) or hasattr(o, "_Body"):
            continue
        if not _has_solids(getattr(o, "Shape", None)):
            continue
        try:
            gp = str(o.getGlobalPlacement())
        except Exception:
            try:
                gp = str(o.Placement)
            except Exception:
                gp = ""
        vals.append((o.Name, gp))
    return tuple(vals)


# ---------------------------------------------------------------------------
# Toggle handling and automatic updates
# ---------------------------------------------------------------------------

def set_active(on):
    on = bool(on)
    _cancel_debounce()
    if on:
        if _state["active"] and _doc_alive(_state.get("doc")):
            # Already active: an "ON" in a different active document re-binds
            # the detector to the document the user is looking at.
            target = FreeCAD.ActiveDocument
            if target is not None and target.Name != _state["doc"].Name:
                _restore(_state["doc"])
                _state["doc"] = target
                _saved.clear()
                _state["last_fp"] = None
                _refresh()
            return _state["active"]
        if _state["active"] == on:
            return _state["active"]
        _state["active"] = True
        doc = _current_doc()
        if doc is None:
            _msg("PartDesignUpgrade: open a document first, then enable the detector.")
            _state["active"] = False
            try:
                Gui.updateGuiCommand(_CMD_NAME)
            except Exception:
                pass
            return False
        _saved.clear()
        _state["last_fp"] = None
        _start_watchdog()
        _refresh()
    else:
        _stop_watchdog()
        doc = _state.get("doc")
        if _doc_alive(doc):
            _restore(doc)
        _saved.clear()
        _state["doc"] = None
        _state["active"] = False
        _notify_off()
    return _state["active"]


def toggle():
    return set_active(not _state["active"])


class _CDObserver:
    """Document observer: schedules a debounced re-detection after any change,
    except for changes caused by our own visual updates. FreeCAD keeps the
    observer installed permanently, so it just early-returns when inactive."""

    def slotCreatedObject(self, obj):
        self._changed()

    def slotDeletedObject(self, obj):
        if obj is not None and obj == _state.get("doc"):
            try:
                set_active(False)
            except Exception:
                pass
        self._changed()

    def slotChangedObject(self, obj, prop):
        self._changed()

    def slotRecomputed(self, doc):
        self._changed()

    def _changed(self):
        if _state["active"] and not _state["refreshing"]:
            _schedule()


def _get_observer():
    global _observer
    if _observer is None:
        _observer = _CDObserver()
    return _observer


# -- debounced refresh (document observer) --------------------------------

def _schedule():
    _cancel_debounce()
    global _timer
    if _timer is None:
        if not hasattr(Gui, "getMainWindow"):
            return
        mw = Gui.getMainWindow()
        if mw is None:
            return
        _timer = QtCore.QTimer(mw)
        _timer.setSingleShot(True)
        _timer.timeout.connect(_refresh)
    _timer.start(_DEBOUNCE_MS)


def _cancel_debounce():
    global _timer
    if _timer is not None:
        try:
            _timer.stop()
        except Exception:
            pass


# -- watchdog (moves not seen by the observer) ----------------------------

def _watchdog_tick():
    if not _state["active"]:
        return
    doc = _current_doc()
    if doc is None:
        return
    try:
        fp = _fingerprint(doc)
    except Exception:
        return
    if fp != _state.get("last_fp"):
        _refresh()


def _start_watchdog():
    _stop_watchdog()
    global _watchdog
    if not hasattr(Gui, "getMainWindow"):
        return
    mw = Gui.getMainWindow()
    if mw is None:
        return
    _watchdog = QtCore.QTimer(mw)
    _watchdog.timeout.connect(_watchdog_tick)
    _watchdog.start(_WATCHDOG_MS)


def _stop_watchdog():
    global _watchdog
    if _watchdog is not None:
        try:
            _watchdog.stop()
        except Exception:
            pass
        _watchdog = None