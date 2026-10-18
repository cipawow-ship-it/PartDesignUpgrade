# -*- coding: utf-8 -*-
"""PartDesignUpgrade GUI init: registers a lightweight workbench. The buttons
also appear in the standalone "AddOn Tools" toolbar group provided by the
CollisionDetector addon and can be moved anywhere on the top bars."""

import FreeCADGui as Gui

from . import commands
from .translations import tr as _tr


class PartDesignUpgradeWorkbench(Gui.Workbench):
    """Container workbench so FreeCAD integrates the addon normally; the real
    UI lives in the Part Design Helper Features toolbar."""

    MenuText = _tr("Part Design Upgrade")
    ToolTip = _tr("PartDesign helpers: pipe, subtractive pipe, rib, assembly cut, symmetry mirror, weight/volume")

    def Initialize(self):
        cmds = [
            "PartDesignUpgrade_Pipe",
            "PartDesignUpgrade_SubtractPipe",
            "PartDesignUpgrade_FaceRib",
            "PartDesignUpgrade_Cut",
            "PartDesignUpgrade_AutoMirror",
            "PartDesignUpgrade_Weight",
        ]
        self.appendToolbar("PartDesignUpgrade", cmds)
        self.appendMenu("PartDesignUpgrade", cmds)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(PartDesignUpgradeWorkbench())