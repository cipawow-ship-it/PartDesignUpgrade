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

_OLD_TOOLBAR_NAME = "AssemblyCutToolBar"
_OLD_COMMAND = "AssemblyCut_Cut"
_SWEEP_DELAY_MS = 5000

_notified = False


def _detect_legacy():
    """True when the standalone AssemblyCut addon is actually loaded.

    On FreeCAD 1.x `Gui.Command` is a plain type whose registry is queried via
    `listAll()`. Guarded so this works even in headless mode, where the
    `Command` attribute does not exist at all.
    """
    gcmd = getattr(Gui, "Command", None)
    if gcmd is None:
        return False
    try:
        return _OLD_COMMAND in list(getattr(gcmd, "listAll", lambda: [])() or [])
    except Exception:
        return False


def _hook_legacy_engine():
    """Make the legacy AssemblyCut_Cut command run the PartDesignUpgrade engine.

    re-registering the command is not possible on FreeCAD 1.x: `Gui.addCommand`
    silently keeps the existing registration and there is no API to remove a
    non-custom command. The legacy command's `Activated` dispatches through
    ``from <core> import assembly_cut`` at call time, so replacing that symbol
    on the already-loaded core module redirects every invocation (macros,
    custom toolbars, keyboard shortcuts) to the new engine. Both the modern
    package layout (`freecad.AssemblyCut.AssemblyCutCore`) and the old zip
    layout (top-level `AssemblyCutCore`) are supported.
    """
    global _notified
    if not _detect_legacy():
        return False
    try:
        from . import assemblycut
    except Exception:
        return False
    entry = getattr(assemblycut, "assembly_cut", None)
    if entry is None:
        return False
    try:
        import freecad.AssemblyCut.AssemblyCutCore as _core
    except Exception:
        try:
            import AssemblyCutCore as _core
        except Exception:
            _core = None
    if _core is None:
        return False
    if getattr(_core, "assembly_cut", None) is entry:
        return True
    _core.assembly_cut = entry
    if not _notified:
        _notified = True
        FreeCAD.Console.PrintMessage(
            "AssemblyCut is now part of PartDesignUpgrade: you can uninstall "
            "the standalone 'AssemblyCut' addon (the legacy AssemblyCut_Cut "
            "command now runs the PartDesignUpgrade engine).\n")
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
        _hook_legacy_engine()
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