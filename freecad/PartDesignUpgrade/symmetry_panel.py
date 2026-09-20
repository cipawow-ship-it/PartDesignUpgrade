# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Symmetry panel shown in a floating dock.

The reference (plane / axis / point and its offset) is chosen in the "Mirror
(Symmetry)" task dialog. Once the dialog is accepted, the dock with the panel
opens (floating, movable window):
- "Mirror last operation" mirrors the latest feature of the body,
- "Auto mirror" polls every 150 ms and mirrors every new feature as it
  appears, without ever touching already built features (so edge/face
  references keep working, unlike a full re-dress of the transform chain).
Closing the dock hides the symmetry reference datum. The 3D view is kept
clean by hiding the intermediate body features: only the Tip stays visible.
"""

import FreeCAD

try:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import (QCheckBox, QHBoxLayout,
                                   QLabel, QPushButton, QVBoxLayout, QWidget)
except ImportError:
    from PySide2.QtCore import QTimer
    from PySide2.QtWidgets import (QCheckBox, QHBoxLayout,
                                   QLabel, QPushButton, QVBoxLayout, QWidget)

from . import symmetry
from .translations import tr as _tr

_panel = None
_task = None


class SymmetryPanel(QWidget):
    """Sidebar widget that toggles the mirror and auto-mirrors new features."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc = None
        self.body = None
        self._broken = False
        self._auto_enabled = False
        self._known_features = set()
        self._failed_features = set()
        self._busy = False

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        ref_row = QHBoxLayout()
        self.ref_lbl = QLabel("")
        self.ref_lbl.setStyleSheet("color: #888;")
        ref_row.addWidget(self.ref_lbl)
        ref_row.addStretch(1)
        root.addLayout(ref_row)

        self.btn_last = QPushButton(_tr("Mirror last operation"))
        self.btn_last.setToolTip(_tr(
            "Mirror the last feature in the body tree. If a symmetry already "
            "exists it is updated to include the latest feature."))
        self.btn_last.clicked.connect(self._on_mirror_last)
        root.addWidget(self.btn_last)

        self.chk_auto = QCheckBox(_tr("Auto mirror"))
        self.chk_auto.setToolTip(_tr(
            "When on, every new feature of the body is mirrored "
            "automatically."))
        self.chk_auto.setChecked(False)
        self.chk_auto.toggled.connect(self._on_auto_toggled)
        root.addWidget(self.chk_auto)

        self.info = QLabel("")
        self.info.setWordWrap(True)
        self.info.setStyleSheet("color: #555;")
        root.addWidget(self.info)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._set_info()

    # ------------------------------------------------------------- actions

    def _on_mirror_last(self):
        if self.body is None or self.doc is None:
            return
        self._sync_body_from_selection()
        symmetry.mirror_last_operation(self.doc, self.body)
        self._set_info()

    def _on_auto_toggled(self, on):
        if on:
            self._start_auto()
        else:
            self._stop_auto()
        self._set_info()

    # --------------------------------------------------------------- auto

    def _start_auto(self):
        self._sync_body_from_selection()
        self._known_features = set(
            f.Name for f in symmetry._real_features(self.body)) \
            if self.body is not None else set()
        self._failed_features = set()
        self._auto_enabled = True
        self._timer.start(150)
        _auto_msg(_tr("Auto mirror is on."))

    def _stop_auto(self):
        self._timer.stop()
        self._auto_enabled = False
        _auto_msg(_tr("Auto mirror is off."))

    def _poll(self):
        if not self._auto_enabled or self._busy:
            return
        if self.body is None or self.doc is None:
            self._stop_auto()
            return
        self._sync_body_from_selection()
        try:
            if self.body.Name not in [o.Name for o in self.doc.Objects]:
                self._stop_auto()
                return
        except Exception:
            return
        try:
            # never re-enter a running recompute: a recursive call is a no-op
            # that leaves the shape unstable, so the mirror would be invalid.
            # Wait for the next tick instead.
            if getattr(self.doc, "Recomputing", False):
                return
            self.doc.recompute()
        except Exception:
            pass
        # Only mirror once the body is fully updated.
        try:
            state = self.body.State
            if "Touched" in state or "Invalid" in state:
                return
        except Exception:
            pass
        self._mirror_new_features()
        tip = getattr(self.body, "Tip", None)
        if tip is not None:
            symmetry.sync_visibility(self.doc.Name, self.body.Name, tip.Name)

    def _mirror_new_features(self):
        if self.body is None or self.doc is None:
            return
        ref = symmetry.find_reference(self.doc, self.body)
        if ref is None:
            return
        # mirror new features in body-tree order (not alphabetically) so a
        # feature is never mirrored before the one it depends on
        new_feats = [
            f for f in symmetry._real_features(self.body)
            if f.Name not in self._known_features
            and f.Name not in self._failed_features]
        if not new_feats:
            return
        self._busy = True
        try:
            for feat in new_feats:
                if not symmetry._is_transform_feature(feat):
                    self._known_features.add(feat.Name)
                    continue
                try:
                    s = feat.Shape
                    if s is None or s.isNull() or not s.isValid() or not s.Solids:
                        continue  # not built/stable yet: retry next tick
                except Exception:
                    continue
                try:
                    tip = self.body.Tip
                    ts = tip.Shape
                    if tip is None or ts is None or ts.isNull() or not ts.isValid():
                        continue  # body still rebuilding: retry next tick
                except Exception:
                    continue
                if symmetry.mirror_feature(self.doc, self.body, ref, feat):
                    self._known_features.add(feat.Name)
                else:
                    # do not retry a feature that genuinely cannot be mirrored
                    self._failed_features.add(feat.Name)
        finally:
            self._busy = False

    # --------------------------------------------------------------- info

    def _set_info(self):
        if self._broken:
            self.info.setText(_tr(
                "No valid body. Select a PartDesign body and open the panel again."))
            self.ref_lbl.setText("")
            return
        ch = symmetry._last_choice or {}
        kind = ch.get("kind", "plane")
        target = ch.get("target", "XY")
        if kind == "plane":
            ref_txt = _tr("Plane {}".format(target))
        elif kind == "axis":
            ref_txt = _tr("Axis {}".format(target))
        else:
            ref_txt = _tr("Point")
        self.ref_lbl.setText("{}".format(ref_txt))
        if self.chk_auto.isChecked():
            self.info.setText(_tr(
                "Auto mirror: every new feature is mirrored."))
        else:
            self.info.setText(_tr(
                "Mirror the last operation, or enable auto mirror."))

    # ------------------------------------------------------------- lifecycle

    def rebind(self, doc, body):
        self.doc = doc
        self.body = body
        self._broken = body is None
        if body is None:
            self._stop_auto()
        self._known_features = set(
            f.Name for f in symmetry._real_features(body)) \
            if body is not None else set()
        self._set_info()

    def _sync_body_from_selection(self):
        """Follow the body the user selected, so the panel works on it even
        when it was opened on another body."""
        if self.doc is None:
            return
        try:
            import FreeCADGui as Gui
            if not Gui.Selection.getSelection():
                return
            b = symmetry._active_body(self.doc)
        except Exception:
            return
        if b is None or b is self.body:
            return
        self.body = b
        self._broken = False
        self._known_features = set(
            f.Name for f in symmetry._real_features(b))
        self._failed_features = set()
        self._set_info()

    def closeEvent(self, event):
        self._stop_auto()
        event.accept()


# ------------------------------------------------------------- dock owner


_dock = None


def _make_dock():
    """Create the non-modal dock that hosts the SymmetryPanel.

    The dock starts floating (a movable window), so it never pushes the side
    panels around or creates an extra bar."""
    global _dock
    import FreeCADGui
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QDockWidget
    mw = FreeCADGui.getMainWindow()
    dock = QDockWidget(_tr("Symmetry"), mw)
    dock.setObjectName("SymmetryPanelDock")
    dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable
                     | QDockWidget.DockWidgetFeature.DockWidgetMovable
                     | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
    dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea
                         | Qt.DockWidgetArea.RightDockWidgetArea)
    dock.setWidget(_panel)
    dock.resize(280, 170)
    dock.visibilityChanged.connect(_on_dock_visibility)
    # Start as a free-floating window, bottom-left of the 3D view, so it
    # does not create a second side bar.
    dock.setFloating(True)
    try:
        from PySide6.QtGui import QCursor
        view = mw.activeWindow()
        if view is not None:
            mw.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
            dock.setFloating(True)
            gp = view.mapToGlobal(view.rect().bottomLeft())
            dock.move(gp.x() + 20, gp.y() - dock.height() - 20)
        else:
            mw.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
    except Exception:
        mw.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
    _dock = dock
    return dock


def _on_dock_visibility(visible):
    global _panel, _dock
    if not visible:
        # During a re-dock transition the signal fires with False even though
        # the window stays visible. Defer the check: only when the dock is
        # still hidden after the event loop do we really shut down.
        try:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(50, _really_hidden_check)
        except Exception:
            pass
    elif _panel is not None:
        try:
            symmetry.show_reference(_panel.doc)
        except Exception:
            pass


def _really_hidden_check():
    global _panel, _dock
    if _dock is not None and _dock.isVisible():
        return
    if _panel is not None:
        _panel._stop_auto()
        # Closing the panel ends the symmetry session: the next time the
        # command is run, ask for a new symmetry plane instead of silently
        # reusing the previous one. The geometry is left untouched.
        try:
            symmetry._force_new_reference = True
            symmetry.hide_reference(_panel.doc)
        except Exception:
            pass


def show_symmetry_dock(doc, body=None, enabled=None):
    """Show the non-modal symmetry panel dock (does not block FreeCAD)."""
    global _panel, _dock
    if body is None and doc is not None:
        from .symmetry import _active_body
        body = _active_body(doc)
    if _panel is None:
        _panel = SymmetryPanel()
    _panel.rebind(doc, body)
    try:
        symmetry.show_reference(doc)
    except Exception:
        pass
    if _dock is None:
        try:
            _dock = _make_dock()
        except Exception as exc:
            import traceback
            FreeCAD.Console.PrintError(
                "Symmetry panel: dock creation failed: {}\n{}\n".format(
                    exc, traceback.format_exc()))
            _dock = None
    if _dock is not None:
        _dock.show()
        _dock.raise_()
    if enabled is not None:
        _panel.chk_auto.blockSignals(True)
        _panel.chk_auto.setChecked(bool(enabled))
        _panel.chk_auto.blockSignals(False)
        if enabled:
            _panel._start_auto()
        else:
            _panel._stop_auto()
    return _panel


def hide_symmetry_dock():
    global _dock
    if _dock is not None:
        _dock.hide()


def run_symmetry_panel(doc, body=None, enabled=None, raise_=True):
    """Backward-compatible entry point: shows the non-modal dock."""
    return show_symmetry_dock(doc, body, enabled)


def sync_panel():
    """Refresh the panel state from the current document/body."""
    global _panel
    if _panel is not None:
        _panel._set_info()


def _auto_msg(text):
    try:
        FreeCAD.Console.PrintMessage(text + "\n")
    except Exception:
        pass