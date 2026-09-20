# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Legacy-addon compatibility sweep for PartDesignUpgrade.

PartDesignUpgrade was grown out of the standalone "AssemblyCut" addon. When a
user keeps that old addon installed (it is distributed as a zip without a
package.xml), starting PartDesignUpgrade would show two "Assembly Cut" buttons
(an injected *Assembly Cut* toolbar plus the *Cut* button of this addon) and
two code paths doing the same job.

This module removes that duplication at runtime:
  - it hides/removes the old addon's injected "AssemblyCutToolBar";
  - it re-points the old "AssemblyCut_Cut" command at this addon's engine, so
    macros and custom toolbars that still invoke the legacy command keep
    working with the fixed implementation;
  - it prints a one-off console notice telling the user they can uninstall the
    old addon.

The sweep is deliberately scheduled a few seconds after startup because the
legacy addon injects its toolbar with a 3 s timer of its own.
"""

import os

import FreeCAD
import FreeCADGui as Gui

from .translations import tr as _tr

_OLD_TOOLBAR_NAME = "AssemblyCutToolBar"
_OLD_COMMAND = "AssemblyCut_Cut"
_SWEEP_DELAY_MS = 5000

_notified = False


def _icon(name):
    return os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
        "Resources", "Icons", name)


def _delegate_old_command():
    """Re-point the legacy AssemblyCut_Cut command at the new engine.

    Only done when the legacy command is actually registered (i.e. the old
    addon is really loaded), so a PartDesignUpgrade-only install is never
    touched. Overwriting an already registered command is safe here: FreeCAD
    keeps the last registration, and this sweep runs after the legacy addon.
    """
    global _notified
    gcmd = getattr(Gui, "Command", None)
    if gcmd is None:
        return False
    try:
        has_old = gcmd.has(_OLD_COMMAND)
    except Exception:
        has_old = False
    if not has_old:
        return False
    try:
        from . import assemblycut
    except Exception:
        return False
    entry = getattr(assemblycut, "assembly_cut", None)
    if entry is None:
        return False

    class _LegacyCompatCommand:
        def GetResources(self):
            return {
                "MenuText": _tr("Assembly Cut"),
                "ToolTip": _tr(
                    "Cut several PartDesign bodies at once using one sketch "
                    "(now provided by PartDesignUpgrade)."),
                "StatusTip": _tr("Cut multiple bodies with a single sketch"),
                "Pixmap": _icon("AssemblyCut.svg"),
            }

        def IsActive(self):
            try:
                return FreeCAD.ActiveDocument is not None
            except Exception:
                return False

        def Activated(self, arg=0):
            entry()

    try:
        gcmd.addCommand(_OLD_COMMAND, _LegacyCompatCommand())
    except Exception:
        return False
    if not _notified:
        _notified = True
        FreeCAD.Console.PrintMessage(
            "AssemblyCut is now part of PartDesignUpgrade: you can uninstall "
            "the standalone 'AssemblyCut' addon.\n")
    return True


def _sweep():
    """Remove the legacy Assembly Cut toolbar and bind its command to the new
    engine. All failures are swallowed: this is only a convenience cleanup."""
    try:
        main = Gui.getMainWindow()
        if main is not None:
            from PySide.QtWidgets import QToolBar
            for tb in main.findChildren(QToolBar):
                if tb.objectName() != _OLD_TOOLBAR_NAME:
                    continue
                try:
                    main.removeToolBar(tb)
                    tb.deleteLater()
                except Exception:
                    pass
    except Exception:
        pass
    try:
        _delegate_old_command()
    except Exception:
        pass


def schedule():
    """Arrange the legacy sweep once, shortly after startup."""
    _sweep()
    try:
        from PySide import QtCore

        timer = QtCore.QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(_sweep)
        timer.start(_SWEEP_DELAY_MS)
        # keep a reference so the timer is not garbage-collected
        schedule._timer = timer
    except Exception:
        pass