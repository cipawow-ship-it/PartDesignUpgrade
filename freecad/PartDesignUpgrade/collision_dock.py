# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
"""PartDesignUpgrade collision detector side dock: a window on the left that
reports either "no collision" or the colliding pairs with their overlap volume.

The dock is only meant to be visible while the detector is on. To guarantee it
never flashes (or stays) after a FreeCAD restart, it is not part of the main
window's dock layout at startup at all: it is attached on first use and
un-attached again when closed, so FreeCAD's layout restore has nothing to
reopen.
"""

import FreeCADGui as Gui

from PySide import QtCore
from PySide.QtWidgets import (
    QDockWidget, QTextEdit, QVBoxLayout, QWidget,
)

from .translations import tr as _tr

_name = None
_dock = None


class CollisionDock(QDockWidget):
    """Read-only report panel placed on the left side of the main window."""

    def __init__(self, parent):
        super(CollisionDock, self).__init__(_tr("Collision Detector"), parent)
        self.setObjectName("CollisionDetectorDock")
        self.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable)
        self.setFloating(True)

        body = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setMinimumHeight(140)
        layout.addWidget(self.text)
        body.setLayout(layout)
        self.setWidget(body)
        self.set_report(
            _tr("Switch the detector on (the Collision Detector button) to start."))

    def set_report(self, text):
        try:
            self.text.setPlainText(text)
        except Exception:
            pass

    def _attach(self):
        """Join the main window layout once, immediately before being shown."""
        get = getattr(Gui, "getMainWindow", None)
        if get is None:
            return
        main = get()
        if main is None:
            return
        try:
            if int(main.dockWidgetArea(self)) == 0:  # not attached
                main.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)
        except Exception:
            main.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)

    def _detach(self):
        """Leave the main window layout so FreeCAD never restores it."""
        get = getattr(Gui, "getMainWindow", None)
        if get is None:
            return
        main = get()
        if main is None:
            return
        try:
            main.removeDockWidget(self)
        except Exception:
            pass

    def closeEvent(self, event):
        # Keep the dock alive in the background (so the toggle can re-show it)
        # but take it out of the layout so no later window-state restore can
        # reopen it.
        try:
            self.hide()
            self._detach()
        except Exception:
            pass
        event.accept()


def _get_name():
    global _name
    if _name is None:
        _name = "PartDesignUpgrade: report dock"
    return _name


def ensure_dock():
    """Create the dock widget once (hidden, NOT attached to the main window
    layout) and return it. Returns None in headless mode where no main window
    exists."""
    global _dock
    if _dock is not None:
        return _dock
    get = getattr(Gui, "getMainWindow", None)
    if get is None:
        return None
    main = get()
    if main is None:
        return None
    _dock = CollisionDock(main)
    _dock.hide()
    return _dock


def show_report(text):
    d = ensure_dock()
    if d is None:
        return
    d.set_report(text)
    d._attach()
    d.setFloating(True)
    d.show()
    d.raise_()


def show(text=None):
    d = ensure_dock()
    if d is None:
        return
    if text is not None:
        d.set_report(text)
    d._attach()
    d.setFloating(True)
    d.show()
    d.raise_()


def hide_report():
    d = ensure_dock()
    if d is not None:
        d.hide()


def set_report_callback(core_module):
    """Wire collision_core to push every recalculation result into the dock
    (and to show the dock whenever a report is ready); deactivation hides it.

    The dock is deliberately NOT created here: if a CollisionDock widget exists
    as a child of the main window at startup, QMainWindow.restoreState would
    re-attach and re-show it on the next session even if it was hidden. Creating
    it lazily (only when the detector first produces a report) guarantees the
    window simply does not exist while FreeCAD loads, so it can never flash."""
    core_module.set_report_sink(show_report)
    core_module.set_off_sink(hide_report)