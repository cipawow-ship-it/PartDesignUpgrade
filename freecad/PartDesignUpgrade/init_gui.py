# -*- coding: utf-8 -*-
"""PartDesignUpgrade GUI init: registers a lightweight workbench and injects
its three buttons into the Part Design Helper Features toolbar."""

import FreeCADGui as Gui

from . import commands
from .Manipulator import PartDesignUpgradeManipulator
from .translations import tr as _tr


class PartDesignUpgradeWorkbench(Gui.Workbench):
    """Container workbench so FreeCAD integrates the addon normally; the real
    UI lives in the Part Design Helper Features toolbar."""

    MenuText = _tr("Part Design Upgrade")
    ToolTip = _tr("PartDesign helpers: pipe, assembly cut and weight/volume")

    def Initialize(self):
        cmds = [
            "PartDesignUpgrade_Pipe",
            "PartDesignUpgrade_SubtractPipe",
            "PartDesignUpgrade_Cut",
            "PartDesignUpgrade_Weight",
        ]
        self.appendToolbar("PartDesignUpgrade", cmds)
        self.appendMenu("PartDesignUpgrade", cmds)

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(PartDesignUpgradeWorkbench())
Gui.addWorkbenchManipulator(PartDesignUpgradeManipulator())